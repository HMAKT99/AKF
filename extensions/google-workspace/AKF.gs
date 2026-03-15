/**
 * AKF metadata storage, audit, and detection logic for Google Workspace.
 *
 * Storage: PropertiesService.getDocumentProperties().getProperty('akf_metadata')
 *
 * Note: Document Properties don't survive export-to-DOCX. They persist only
 * within the Google Workspace ecosystem. For DOCX interop, use the Python CLI
 * to re-embed after export.
 */

var AKF_PROPERTY_KEY = 'akf_metadata';

var AUTHORITY_WEIGHTS_GS = { 1: 1.0, 2: 0.85, 3: 0.7, 4: 0.5, 5: 0.3 };

// v1.1 origin weights (matches Python trust.py)
var ORIGIN_WEIGHTS_GS = {
  'human': 1.0, 'ai_supervised_by_human': 0.9, 'collaboration': 0.85,
  'human_assisted_by_ai': 0.85, 'ai': 0.7, 'multi_agent': 0.6, 'ai_chain': 0.5
};

var GROUNDING_BONUS_GS = 0.05; // per evidence, max 0.15
var REVIEW_BONUS_GS = { 'approved': 0.1, 'needs_changes': 0.0, 'rejected': -0.2 };

// Matches Python security.py HIERARCHY
var CLASSIFICATION_RANK = {
  'public': 0, 'internal': 1, 'confidential': 2, 'highly-confidential': 3, 'restricted': 4
};

/**
 * v1.1 trust computation — matches Python trust.py effective_trust().
 */
function effectiveTrustGs(claim) {
  var tier = claim.authority_tier || 3;
  var authority = AUTHORITY_WEIGHTS_GS[tier] || 0.7;

  // Origin weight
  var originWeight = 1.0;
  if (claim.origin) {
    var originType = typeof claim.origin === 'string' ? claim.origin : (claim.origin.type || 'ai');
    originWeight = ORIGIN_WEIGHTS_GS[originType] || 0.7;
  }

  var score = claim.confidence * authority * originWeight;

  // Grounding bonus: +0.05 per evidence, max 0.15
  var evCount = (claim.evidence && claim.evidence.length) ? claim.evidence.length : 0;
  score += Math.min(evCount * GROUNDING_BONUS_GS, 0.15);

  // Review bonus
  if (claim.reviews && claim.reviews.length) {
    for (var i = 0; i < claim.reviews.length; i++) {
      var verdict = claim.reviews[i].verdict || 'approved';
      score += REVIEW_BONUS_GS[verdict] || 0;
    }
  }

  // Clamp to [0, 1]
  score = Math.max(0, Math.min(1, score));

  var decision;
  if (score >= 0.7) decision = 'ACCEPT';
  else if (score >= 0.4) decision = 'LOW';
  else decision = 'REJECT';
  return { score: score, decision: decision };
}

/**
 * Normalize compact wire format keys to descriptive field names.
 */
function normalizeMetaGs(raw) {
  if (!raw) return raw;
  var TOP_MAP = { v: 'version', ver: 'version', label: 'classification', cls: 'classification', prov: 'provenance', hash: 'integrity_hash', by: 'author', at: 'created' };
  var CLAIM_MAP = { c: 'content', t: 'confidence', src: 'source', tier: 'authority_tier', ai: 'ai_generated', ver: 'verified' };

  var keys = [];
  var key;
  for (key in TOP_MAP) keys.push(key);
  for (var i = 0; i < keys.length; i++) {
    key = keys[i];
    if (raw[key] !== undefined && raw[TOP_MAP[key]] === undefined) {
      raw[TOP_MAP[key]] = raw[key];
      delete raw[key];
    }
  }

  var claims = raw.claims;
  if (claims && claims.length) {
    var claimKeys = [];
    for (key in CLAIM_MAP) claimKeys.push(key);
    for (var j = 0; j < claims.length; j++) {
      for (var k = 0; k < claimKeys.length; k++) {
        key = claimKeys[k];
        if (claims[j][key] !== undefined && claims[j][CLAIM_MAP[key]] === undefined) {
          claims[j][CLAIM_MAP[key]] = claims[j][key];
          delete claims[j][key];
        }
      }
    }
  }

  return raw;
}

function getAKFMetadata() {
  var props = PropertiesService.getDocumentProperties();
  var raw = props.getProperty(AKF_PROPERTY_KEY);
  if (!raw) return null;
  try {
    return normalizeMetaGs(JSON.parse(raw));
  } catch (e) {
    return null;
  }
}

function setAKFMetadata(meta) {
  var props = PropertiesService.getDocumentProperties();
  props.setProperty(AKF_PROPERTY_KEY, JSON.stringify(meta));
}

function embedMetadata() {
  var existing = getAKFMetadata();
  if (existing) return existing;

  var email = Session.getActiveUser().getEmail();
  var meta = {
    version: '1.0',
    id: Utilities.getUuid(),
    author: email,
    classification: 'internal',
    claims: [],
    provenance: [
      {
        hop: 1,
        actor: email,
        action: 'created',
        timestamp: new Date().toISOString()
      }
    ]
  };

  setAKFMetadata(meta);
  return meta;
}

function addClaim(claimData) {
  if (!claimData || !claimData.content || String(claimData.content).trim().length === 0) {
    throw new Error('Claim content is required');
  }
  var conf = parseFloat(claimData.confidence) || 0.8;
  if (conf < 0 || conf > 1) throw new Error('Confidence must be between 0 and 1');

  var meta = getAKFMetadata();
  if (!meta) meta = embedMetadata();

  var claim = {
    id: Utilities.getUuid(),
    content: String(claimData.content).trim(),
    confidence: conf,
    authority_tier: 3,
    source: claimData.source ? String(claimData.source).trim() : undefined,
    ai_generated: !!claimData.ai_generated,
    risk: (claimData.ai_generated && claimData.risk) ? String(claimData.risk).trim() : undefined
  };

  if (!meta.claims) meta.claims = [];
  meta.claims.push(claim);

  if (!meta.provenance) meta.provenance = [];
  var email = Session.getActiveUser().getEmail();
  meta.provenance.push({
    hop: meta.provenance.length + 1,
    actor: email,
    action: 'claim_added',
    timestamp: new Date().toISOString(),
    claims_added: [claim.id]
  });

  setAKFMetadata(meta);
  return claim;
}

function auditMetadata(meta) {
  if (!meta) meta = getAKFMetadata();
  if (!meta) return { compliant: false, score: 0, checks: [], recommendations: ['No metadata found'] };

  var checks = [];
  var scorePoints = 0;
  var maxPoints = 0;
  var recommendations = [];

  maxPoints++;
  var hasProv = meta.provenance && meta.provenance.length > 0;
  checks.push({ check: 'provenance_present', passed: !!hasProv });
  if (hasProv) scorePoints++;
  else recommendations.push('Add provenance to track data lineage');

  maxPoints++;
  var hasHash = !!meta.integrity_hash;
  checks.push({ check: 'integrity_hash', passed: hasHash });
  if (hasHash) scorePoints++;
  else recommendations.push('Compute integrity hash for tamper detection');

  maxPoints++;
  var hasClass = !!meta.classification;
  checks.push({ check: 'classification_set', passed: hasClass });
  if (hasClass) scorePoints++;
  else recommendations.push('Set security classification');

  maxPoints++;
  var claims = meta.claims || [];
  var allSourced = claims.length === 0 || claims.every(function(c) {
    return c.source && c.source !== 'unspecified';
  });
  checks.push({ check: 'all_claims_sourced', passed: allSourced });
  if (allSourced) scorePoints++;
  else recommendations.push('Add source attribution to all claims');

  maxPoints++;
  var aiLabeled = claims.every(function(c) {
    return c.ai_generated !== undefined;
  });
  checks.push({ check: 'ai_claims_labeled', passed: aiLabeled });
  if (aiLabeled) scorePoints++;

  maxPoints++;
  var riskyAi = claims.filter(function(c) {
    return c.ai_generated && (c.authority_tier || 3) >= 4;
  });
  var allRiskyDescribed = riskyAi.length === 0 || riskyAi.every(function(c) { return !!c.risk; });
  checks.push({ check: 'ai_risk_described', passed: allRiskyDescribed });
  if (allRiskyDescribed) scorePoints++;
  else recommendations.push('Add risk descriptions to AI-generated speculative claims');

  maxPoints++;
  var validStructure = claims.length > 0 && claims.every(function(c) {
    return c.content && c.confidence >= 0 && c.confidence <= 1;
  });
  checks.push({ check: 'valid_structure', passed: validStructure });
  if (validStructure) scorePoints++;

  var score = maxPoints > 0 ? scorePoints / maxPoints : 0;

  return {
    compliant: score >= 0.7,
    score: Math.round(score * 100) / 100,
    checks: checks,
    recommendations: recommendations
  };
}

// ---------------------------------------------------------------------------
// Freshness helpers (matching Python trust.py)
// ---------------------------------------------------------------------------

function getExpiryStringGs(claim) {
  if (claim.expires_at) return claim.expires_at;
  if (claim.freshness && claim.freshness.valid_until) return claim.freshness.valid_until;
  return null;
}

function freshnessStatusGs(claim) {
  var expires = getExpiryStringGs(claim);
  if (!expires) return 'no_expiry';
  try {
    if (new Date().getTime() > new Date(expires).getTime()) return 'expired';
  } catch (e) { return 'no_expiry'; }
  if (!claim.last_verified) return 'stale';
  return 'fresh';
}

// ---------------------------------------------------------------------------
// Detection Class 1: AI Content Without Review
// ---------------------------------------------------------------------------

function detectAiWithoutReviewGs(meta) {
  var findings = [];
  var affected = [];
  var claims = meta.claims || [];

  var aiClaims = claims.filter(function(c) { return c.ai_generated; });
  if (aiClaims.length === 0) {
    return {
      detection_class: 'ai_content_without_review',
      triggered: false, severity: 'info',
      findings: ['No AI-generated claims found'],
      affected_claims: [], recommendation: ''
    };
  }

  // Check unit-level reviews (mirrors Python: unit_has_review = bool(unit.reviews))
  var unitHasReview = meta.reviews && meta.reviews.length > 0;

  for (var i = 0; i < aiClaims.length; i++) {
    var claim = aiClaims[i];
    var claimHasReview = claim.reviews && claim.reviews.length > 0;
    if (!claimHasReview && !unitHasReview) {
      var cid = claim.id || 'unknown';
      affected.push(cid);
      var preview = claim.content.length > 60 ? claim.content.substring(0, 60) + '...' : claim.content;
      findings.push('AI claim [' + cid + '] has no human review: "' + preview + '"');
    }
  }

  var triggered = affected.length > 0;
  return {
    detection_class: 'ai_content_without_review',
    triggered: triggered,
    severity: triggered ? 'high' : 'info',
    findings: findings.length > 0 ? findings : ['All AI content has been reviewed'],
    affected_claims: affected,
    recommendation: triggered ? 'Add human review stamps to AI-generated claims before distribution.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 2: Trust Below Threshold
// ---------------------------------------------------------------------------

function detectTrustBelowThresholdGs(meta) {
  var findings = [];
  var affected = [];
  var claims = meta.claims || [];
  var threshold = 0.7;

  for (var i = 0; i < claims.length; i++) {
    var trust = effectiveTrustGs(claims[i]);
    if (trust.score < threshold) {
      var cid = claims[i].id || 'unknown';
      affected.push(cid);
      findings.push('Claim [' + cid + '] trust ' + trust.score.toFixed(2) + ' < threshold ' + threshold + ' (decision: ' + trust.decision + ')');
    }
  }

  var triggered = affected.length > 0;
  return {
    detection_class: 'trust_below_threshold',
    triggered: triggered,
    severity: triggered ? 'high' : 'info',
    findings: findings.length > 0 ? findings : ['All claims meet trust threshold ' + threshold],
    affected_claims: affected,
    recommendation: triggered ? 'Review low-trust claims and add evidence or human verification.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 3: Hallucination Risk
// ---------------------------------------------------------------------------

function detectHallucinationRiskGs(meta) {
  var findings = [];
  var affected = [];
  var claims = meta.claims || [];

  for (var i = 0; i < claims.length; i++) {
    var claim = claims[i];
    var risks = [];
    var cid = claim.id || 'unknown';

    if (claim.ai_generated && claim.confidence < 0.5) {
      risks.push('low confidence (' + claim.confidence.toFixed(2) + ')');
    }
    if (claim.ai_generated && (!claim.evidence || claim.evidence.length === 0)) {
      risks.push('no evidence grounding');
    }
    if (claim.ai_generated && (!claim.source || claim.source === 'unspecified')) {
      risks.push('no source attribution');
    }
    if (claim.ai_generated && claim.authority_tier !== undefined && claim.authority_tier >= 5) {
      risks.push('lowest authority tier (' + claim.authority_tier + ')');
    }

    if (risks.length > 0) {
      affected.push(cid);
      var preview = claim.content.length > 50 ? claim.content.substring(0, 50) + '...' : claim.content;
      findings.push('Claim [' + cid + '] "' + preview + '": ' + risks.join(', '));
    }
  }

  var triggered = affected.length > 0;
  return {
    detection_class: 'hallucination_risk',
    triggered: triggered,
    severity: triggered ? 'critical' : 'info',
    findings: findings.length > 0 ? findings : ['No hallucination risk indicators found'],
    affected_claims: affected,
    recommendation: triggered ? 'Add evidence grounding, source attribution, and human review to flagged claims.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 4: Knowledge Laundering
// ---------------------------------------------------------------------------

function detectKnowledgeLaunderingGs(meta) {
  var findings = [];
  var affected = [];
  var claims = meta.claims || [];

  if (!meta.classification || meta.classification === 'public') {
    for (var i = 0; i < claims.length; i++) {
      if (claims[i].ai_generated && !claims[i].risk) {
        var cid = claims[i].id || 'unknown';
        affected.push(cid);
        findings.push('AI claim [' + cid + '] in public unit without risk disclosure');
      }
    }
  }

  for (var j = 0; j < claims.length; j++) {
    var claim = claims[j];
    if (claim.ai_generated && claim.authority_tier !== undefined && claim.authority_tier <= 2 && !claim.origin) {
      var cid2 = claim.id || 'unknown';
      if (affected.indexOf(cid2) === -1) {
        affected.push(cid2);
        findings.push('AI claim [' + cid2 + '] has high authority (tier ' + claim.authority_tier + ') but no origin tracking');
      }
    }
  }

  var prov = meta.provenance || [];
  for (var k = 0; k < prov.length; k++) {
    var action = prov[k].action;
    if (action === 'downgraded' || action === 'declassified' || action === 'reclassified') {
      findings.push("Provenance hop by '" + prov[k].actor + "' shows suspicious action: '" + action + "'");
    }
  }

  if (meta.agent) {
    for (var m = 0; m < claims.length; m++) {
      if (claims[m].ai_generated === undefined || claims[m].ai_generated === false) {
        var cid3 = claims[m].id || 'unknown';
        if (affected.indexOf(cid3) === -1) {
          affected.push(cid3);
          findings.push("Unit has agent '" + meta.agent + "' but claim [" + cid3 + "] not labeled as AI-generated");
        }
      }
    }
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'knowledge_laundering',
    triggered: triggered,
    severity: triggered ? 'critical' : 'info',
    findings: findings.length > 0 ? findings : ['No knowledge laundering indicators found'],
    affected_claims: affected,
    recommendation: triggered ? 'Ensure all AI content is properly labeled with origin tracking and risk descriptions.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 5: Classification Downgrade
// ---------------------------------------------------------------------------

function detectClassificationDowngradeGs(meta) {
  var findings = [];
  var prov = meta.provenance || [];

  for (var i = 0; i < prov.length; i++) {
    var action = prov[i].action;
    if (action === 'downgraded' || action === 'declassified' || action === 'reclassified') {
      findings.push("Hop " + i + " by '" + prov[i].actor + "': classification action '" + action + "'");
    }
  }

  if (meta.inherit_classification === false && meta.classification && (meta.classification === 'public' || meta.classification === 'internal')) {
    findings.push("Classification inheritance disabled on '" + meta.classification + "' unit — derived documents can downgrade freely");
  }

  if (meta.allow_external && meta.classification && (CLASSIFICATION_RANK[meta.classification] || 0) >= CLASSIFICATION_RANK['confidential']) {
    findings.push("External sharing enabled on '" + meta.classification + "' unit");
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'classification_downgrade',
    triggered: triggered,
    severity: triggered ? 'critical' : 'info',
    findings: findings.length > 0 ? findings : ['Classification integrity maintained'],
    affected_claims: [],
    recommendation: triggered ? 'Enable inherit_classification and review provenance for unauthorized changes.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 6: Stale Claims (using freshnessStatusGs like Python)
// ---------------------------------------------------------------------------

function detectStaleClaimsGs(meta) {
  var findings = [];
  var affected = [];
  var now = new Date().getTime();
  var claims = meta.claims || [];

  for (var i = 0; i < claims.length; i++) {
    var claim = claims[i];
    var cid = claim.id || 'unknown';

    var status = freshnessStatusGs(claim);
    if (status === 'expired') {
      affected.push(cid);
      findings.push('Claim [' + cid + '] has expired freshness');
    } else if (status === 'stale') {
      affected.push(cid);
      findings.push('Claim [' + cid + '] is stale (past recommended refresh)');
    }

    // Check stale_after_hours from freshness object
    if (claim.freshness && claim.freshness.stale_after_hours && claim.freshness.retrieved_at) {
      try {
        var retrievedMs = new Date(claim.freshness.retrieved_at).getTime();
        var hoursSince = (now - retrievedMs) / (1000 * 60 * 60);
        if (hoursSince > claim.freshness.stale_after_hours) {
          if (affected.indexOf(cid) === -1) affected.push(cid);
          findings.push('Claim [' + cid + '] stale: ' + Math.round(hoursSince) + 'h since retrieval (threshold: ' + claim.freshness.stale_after_hours + 'h)');
        }
      } catch (e) { /* ignore */ }
    }

    if (claim.last_verified) {
      try {
        var verifiedMs = new Date(claim.last_verified).getTime();
        var daysSince = (now - verifiedMs) / (1000 * 60 * 60 * 24);
        if (daysSince > 90) {
          if (affected.indexOf(cid) === -1) affected.push(cid);
          findings.push('Claim [' + cid + '] last verified ' + Math.round(daysSince) + ' days ago');
        }
      } catch (e) { /* ignore */ }
    }
  }

  if (meta.ttl !== undefined && meta.created) {
    try {
      var createdMs = new Date(meta.created).getTime();
      var ageHours = (now - createdMs) / (1000 * 60 * 60);
      if (ageHours > meta.ttl) {
        findings.push('Unit TTL (' + meta.ttl + 'h) exceeded — age is ' + ageHours.toFixed(1) + 'h');
      }
    } catch (e) { /* ignore */ }
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'stale_claims',
    triggered: triggered,
    severity: triggered ? 'medium' : 'info',
    findings: findings.length > 0 ? findings : ['All claims are fresh'],
    affected_claims: affected,
    recommendation: triggered ? 'Refresh expired claims or remove stale content before distribution.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 7: Ungrounded AI Claims
// ---------------------------------------------------------------------------

function detectUngroundedClaimsGs(meta) {
  var findings = [];
  var affected = [];
  var claims = meta.claims || [];

  for (var i = 0; i < claims.length; i++) {
    var claim = claims[i];
    if (!claim.ai_generated) continue;

    var cid = claim.id || 'unknown';
    var issues = [];

    if (!claim.evidence || claim.evidence.length === 0) issues.push('no evidence');
    if (!claim.source || claim.source === 'unspecified') issues.push('no source');
    if (!claim.reasoning) issues.push('no reasoning chain');

    if (issues.length > 0) {
      affected.push(cid);
      var preview = claim.content.length > 50 ? claim.content.substring(0, 50) + '...' : claim.content;
      findings.push('Claim [' + cid + '] "' + preview + '": ' + issues.join(', '));
    }
  }

  var triggered = affected.length > 0;
  return {
    detection_class: 'ungrounded_ai_claims',
    triggered: triggered,
    severity: triggered ? 'high' : 'info',
    findings: findings.length > 0 ? findings : ['All AI claims have grounding'],
    affected_claims: affected,
    recommendation: triggered ? 'Add evidence, source references, or reasoning chains to ungrounded claims.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 8: Trust Degradation Chain
// ---------------------------------------------------------------------------

function detectTrustDegradationChainGs(meta) {
  var findings = [];
  var prov = meta.provenance || [];

  if (prov.length < 2) {
    return {
      detection_class: 'trust_degradation_chain',
      triggered: false, severity: 'info',
      findings: ['No multi-hop provenance chain to evaluate'],
      affected_claims: [], recommendation: ''
    };
  }

  var totalPenalty = 0;
  for (var i = 0; i < prov.length; i++) {
    if (prov[i].penalty !== undefined) totalPenalty += prov[i].penalty;
  }

  if (totalPenalty < -0.1) {
    findings.push('Cumulative provenance penalty: ' + totalPenalty.toFixed(2) + ' across ' + prov.length + ' hops');
  }

  for (var j = 0; j < prov.length; j++) {
    if (prov[j].penalty !== undefined && prov[j].penalty < -0.1) {
      findings.push("Hop " + j + " by '" + prov[j].actor + "' has significant penalty: " + prov[j].penalty.toFixed(2));
    }
  }

  var claims = meta.claims || [];
  for (var k = 0; k < claims.length; k++) {
    var trust = effectiveTrustGs(claims[k]);
    if (trust.score < 0.4 && claims[k].confidence >= 0.7) {
      var cid = claims[k].id || 'unknown';
      findings.push('Claim [' + cid + '] original confidence ' + claims[k].confidence.toFixed(2) + ' degraded to effective trust ' + trust.score.toFixed(2));
    }
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'trust_degradation_chain',
    triggered: triggered,
    severity: triggered ? 'high' : 'info',
    findings: findings.length > 0 ? findings : ['Trust chain is healthy'],
    affected_claims: [],
    recommendation: triggered ? 'Review provenance chain for unnecessary transformations that degrade trust.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 9: Excessive AI Concentration
// ---------------------------------------------------------------------------

function detectExcessiveAiConcentrationGs(meta) {
  var claims = meta.claims || [];
  var total = claims.length;
  var aiCount = 0;
  var humanCount = 0;
  for (var i = 0; i < claims.length; i++) {
    if (claims[i].ai_generated) aiCount++;
    else humanCount++;
  }
  var aiRatio = total > 0 ? aiCount / total : 0;
  var maxAiRatio = 0.8;
  var findings = [];

  if (aiRatio > maxAiRatio) {
    findings.push('AI content ratio ' + Math.round(aiRatio * 100) + '% exceeds threshold ' + Math.round(maxAiRatio * 100) + '% (' + aiCount + '/' + total + ' claims are AI-generated)');
  }

  if (aiCount > 1 && meta.model && aiRatio > maxAiRatio) {
    findings.push('All AI claims attributed to single model: ' + meta.model);
  }

  if (humanCount === 0 && total > 0) {
    findings.push('No human-authored claims — document is entirely AI-generated');
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'excessive_ai_concentration',
    triggered: triggered,
    severity: triggered ? 'medium' : 'info',
    findings: findings.length > 0 ? findings : ['AI concentration ' + Math.round(aiRatio * 100) + '% is within acceptable range'],
    affected_claims: [],
    recommendation: triggered ? 'Add human-authored or human-reviewed claims to balance AI concentration.' : ''
  };
}

// ---------------------------------------------------------------------------
// Detection Class 10: Provenance Gap (1-based hop numbering)
// ---------------------------------------------------------------------------

function detectProvenanceGapGs(meta) {
  var findings = [];
  var prov = meta.provenance || [];

  if (prov.length === 0) {
    findings.push('No provenance chain — content origin is untraceable');
  } else {
    // Check for gaps in hop numbering (1-based: hop 1, 2, 3, ...)
    for (var i = 0; i < prov.length; i++) {
      var expectedHop = i + 1;
      if (prov[i].hop !== expectedHop) {
        findings.push('Provenance gap: expected hop ' + expectedHop + ', found hop ' + prov[i].hop);
      }
    }

    var firstActor = prov[0].actor;
    if (!firstActor || firstActor === 'unknown' || firstActor === 'unspecified') {
      findings.push('Provenance origin actor is unknown or unspecified');
    }

    for (var j = 0; j < prov.length; j++) {
      if (!prov[j].actor) {
        findings.push('Provenance hop ' + j + ' has no actor');
      }
    }
  }

  var claims = meta.claims || [];
  var aiWithoutOrigin = 0;
  for (var k = 0; k < claims.length; k++) {
    if (claims[k].ai_generated && !claims[k].origin) aiWithoutOrigin++;
  }
  if (aiWithoutOrigin > 0) {
    findings.push(aiWithoutOrigin + ' AI claims lack origin tracking');
  }

  var triggered = findings.length > 0;
  return {
    detection_class: 'provenance_gap',
    triggered: triggered,
    severity: triggered ? 'high' : 'info',
    findings: findings.length > 0 ? findings : ['Complete provenance chain with origin tracking'],
    affected_claims: [],
    recommendation: triggered ? 'Add provenance chain and origin tracking to establish content lineage.' : ''
  };
}

// ---------------------------------------------------------------------------
// Aggregate: Run all 10 detection classes
// ---------------------------------------------------------------------------

function runAllDetectionsGs(meta) {
  var results = [
    detectAiWithoutReviewGs(meta),
    detectTrustBelowThresholdGs(meta),
    detectHallucinationRiskGs(meta),
    detectKnowledgeLaunderingGs(meta),
    detectClassificationDowngradeGs(meta),
    detectStaleClaimsGs(meta),
    detectUngroundedClaimsGs(meta),
    detectTrustDegradationChainGs(meta),
    detectExcessiveAiConcentrationGs(meta),
    detectProvenanceGapGs(meta)
  ];

  var triggeredCount = 0;
  var criticalCount = 0;
  var highCount = 0;
  for (var i = 0; i < results.length; i++) {
    if (results[i].triggered) {
      triggeredCount++;
      if (results[i].severity === 'critical') criticalCount++;
      if (results[i].severity === 'high') highCount++;
    }
  }

  return {
    results: results,
    triggered_count: triggeredCount,
    critical_count: criticalCount,
    high_count: highCount,
    clean: triggeredCount === 0
  };
}

function getMetadataForSidebar() {
  var meta = getAKFMetadata();
  if (!meta) return { found: false };
  var auditResult = auditMetadata(meta);
  var detections = runAllDetectionsGs(meta);
  return {
    found: true,
    metadata: meta,
    audit: auditResult,
    detections: detections
  };
}
