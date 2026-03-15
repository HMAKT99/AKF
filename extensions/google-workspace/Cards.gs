/**
 * Card Service UI for the AKF Google Workspace Add-on homepage.
 */

function buildHomepageCard() {
  var meta = getAKFMetadata();

  var card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('AKF Trust Metadata')
        .setSubtitle('Agent Knowledge Format')
    );

  if (!meta) {
    var emptySection = CardService.newCardSection()
      .addWidget(
        CardService.newTextParagraph()
          .setText('No AKF metadata found in this document.')
      )
      .addWidget(
        CardService.newTextButton()
          .setText('Embed Metadata')
          .setOnClickAction(
            CardService.newAction().setFunctionName('onEmbedClick')
          )
      );
    card.addSection(emptySection);
    return card.build();
  }

  // Overview section
  var claims = meta.claims || [];
  var trust = 0;
  if (claims.length > 0) {
    var sum = 0;
    for (var i = 0; i < claims.length; i++) {
      sum += claims[i].confidence || 0;
    }
    trust = sum / claims.length;
  }

  var overviewSection = CardService.newCardSection()
    .setHeader('Overview')
    .addWidget(
      CardService.newDecoratedText()
        .setTopLabel('Classification')
        .setText(meta.classification || 'none')
    )
    .addWidget(
      CardService.newDecoratedText()
        .setTopLabel('Trust Score')
        .setText(trust.toFixed(2))
    )
    .addWidget(
      CardService.newDecoratedText()
        .setTopLabel('Claims')
        .setText(String(claims.length))
    );
  card.addSection(overviewSection);

  // Claims section
  if (claims.length > 0) {
    var claimsSection = CardService.newCardSection().setHeader('Claims');
    for (var j = 0; j < Math.min(claims.length, 10); j++) {
      var c = claims[j];
      var label = c.confidence.toFixed(2);
      if (c.ai_generated) label += ' [AI]';
      if (c.verified) label += ' [verified]';

      claimsSection.addWidget(
        CardService.newDecoratedText()
          .setTopLabel(label)
          .setText(c.content)
          .setWrapText(true)
      );
    }
    card.addSection(claimsSection);
  }

  // Actions
  var actionsSection = CardService.newCardSection()
    .addWidget(
      CardService.newTextButton()
        .setText('Open Sidebar')
        .setOnClickAction(
          CardService.newAction().setFunctionName('showSidebar')
        )
    )
    .addWidget(
      CardService.newTextButton()
        .setText('Run Audit')
        .setOnClickAction(
          CardService.newAction().setFunctionName('onAuditClick')
        )
    )
    .addWidget(
      CardService.newTextButton()
        .setText('Run Detections')
        .setOnClickAction(
          CardService.newAction().setFunctionName('onDetectionClick')
        )
    );
  card.addSection(actionsSection);

  return card.build();
}

function onEmbedClick() {
  embedMetadata();
  return buildHomepageCard();
}

function onAuditClick() {
  var meta = getAKFMetadata();
  if (!meta) return buildHomepageCard();

  var result = auditMetadata(meta);
  var card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Audit Results')
        .setSubtitle(result.compliant ? 'COMPLIANT' : 'NON-COMPLIANT')
    );

  var checksSection = CardService.newCardSection()
    .setHeader('Checks (score: ' + result.score.toFixed(2) + ')');

  for (var i = 0; i < result.checks.length; i++) {
    var check = result.checks[i];
    var icon = check.passed ? '\u2705' : '\u274c';
    checksSection.addWidget(
      CardService.newDecoratedText()
        .setText(icon + ' ' + check.check.replace(/_/g, ' '))
    );
  }
  card.addSection(checksSection);

  if (result.recommendations.length > 0) {
    var recSection = CardService.newCardSection().setHeader('Recommendations');
    for (var j = 0; j < result.recommendations.length; j++) {
      recSection.addWidget(
        CardService.newTextParagraph()
          .setText('\u2022 ' + result.recommendations[j])
      );
    }
    card.addSection(recSection);
  }

  var nav = CardService.newNavigation().pushCard(card.build());
  return CardService.newActionResponseBuilder().setNavigation(nav).build();
}

function onDetectionClick() {
  var meta = getAKFMetadata();
  if (!meta) return buildHomepageCard();

  var report = runAllDetectionsGs(meta);
  var card = buildDetectionCard(report);
  var nav = CardService.newNavigation().pushCard(card);
  return CardService.newActionResponseBuilder().setNavigation(nav).build();
}

function buildDetectionCard(report) {
  var subtitle = report.triggered_count + ' / 10 triggered';
  if (report.critical_count > 0) subtitle += ', ' + report.critical_count + ' critical';
  if (report.high_count > 0) subtitle += ', ' + report.high_count + ' high';

  var card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle('Detection Results')
        .setSubtitle(subtitle)
    );

  var resultsSection = CardService.newCardSection().setHeader('Detections');

  for (var i = 0; i < report.results.length; i++) {
    var r = report.results[i];
    var name = r.detection_class.replace(/_/g, ' ');
    var icon = r.triggered ? '\u26a0' : '\u2713';
    var text = icon + ' ' + name + ' [' + r.severity + ']';

    if (r.triggered && r.findings.length > 0) {
      text += '\n' + r.findings.join('\n');
    }

    resultsSection.addWidget(
      CardService.newTextParagraph().setText(text)
    );
  }

  card.addSection(resultsSection);

  if (report.triggered_count > 0) {
    var recSection = CardService.newCardSection().setHeader('Actions');
    var recs = [];
    for (var j = 0; j < report.results.length; j++) {
      if (report.results[j].triggered && report.results[j].recommendation) {
        recs.push('\u2022 ' + report.results[j].recommendation);
      }
    }
    if (recs.length > 0) {
      recSection.addWidget(
        CardService.newTextParagraph().setText(recs.join('\n'))
      );
    }
    card.addSection(recSection);
  }

  return card.build();
}
