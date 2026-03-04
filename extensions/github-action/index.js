const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Simple glob implementation for .akf files
function findAkfFiles(dir, pattern) {
    const results = [];
    const items = fs.readdirSync(dir, { withFileTypes: true });
    for (const item of items) {
        const fullPath = path.join(dir, item.name);
        if (item.isDirectory() && !item.name.startsWith('.') && item.name !== 'node_modules') {
            results.push(...findAkfFiles(fullPath, pattern));
        } else if (item.isFile() && item.name.endsWith('.akf')) {
            results.push(fullPath);
        }
    }
    return results;
}

function validateAkfFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        const data = JSON.parse(content);

        const errors = [];
        const warnings = [];

        // Check version
        if (!data.v && !data.version) {
            errors.push('Missing version field');
        }

        // Check claims
        if (!Array.isArray(data.claims) || data.claims.length === 0) {
            errors.push('Missing or empty claims array');
        } else {
            for (let i = 0; i < data.claims.length; i++) {
                const claim = data.claims[i];
                const content = claim.c || claim.content;
                const trust = claim.t ?? claim.confidence;

                if (!content) errors.push(`Claim ${i}: missing content`);
                if (trust === undefined || trust === null) errors.push(`Claim ${i}: missing trust score`);
                if (trust < 0 || trust > 1) errors.push(`Claim ${i}: trust score out of range`);

                if (claim.ai || claim.ai_generated) {
                    if (!claim.risk) warnings.push(`Claim ${i}: AI-generated without risk description`);
                }
            }
        }

        // Check classification
        const label = data.label || data.classification;
        const validLabels = ['public', 'internal', 'confidential', 'highly-confidential', 'restricted'];
        if (label && !validLabels.includes(label)) {
            errors.push(`Invalid classification: ${label}`);
        }

        return { valid: errors.length === 0, errors, warnings, data };
    } catch (e) {
        return { valid: false, errors: [`Parse error: ${e.message}`], warnings: [], data: null };
    }
}

// Main
const workspace = process.env.GITHUB_WORKSPACE || '.';
const trustThreshold = parseFloat(process.env.INPUT_TRUST_THRESHOLD || '0.5');
const failOnUntrusted = process.env.INPUT_FAIL_ON_UNTRUSTED === '1' || process.env.INPUT_FAIL_ON_UNTRUSTED === 'true';
const requiredClassification = process.env.INPUT_CLASSIFICATION || '';

const files = findAkfFiles(workspace, '**/*.akf');
console.log(`Found ${files.length} .akf file(s)`);

let hasErrors = false;

for (const file of files) {
    const rel = path.relative(workspace, file);
    const result = validateAkfFile(file);

    if (!result.valid) {
        console.log(`::error file=${rel}::Invalid AKF: ${result.errors.join('; ')}`);
        hasErrors = true;
    } else {
        console.log(`OK: ${rel} (${result.data.claims.length} claims)`);
    }

    for (const warn of result.warnings) {
        console.log(`::warning file=${rel}::${warn}`);
    }

    // Trust threshold check
    if (failOnUntrusted && result.data && result.data.claims) {
        for (const claim of result.data.claims) {
            const trust = claim.t ?? claim.confidence;
            if (trust < trustThreshold) {
                const content = claim.c || claim.content;
                console.log(`::error file=${rel}::Untrusted claim (${trust}): "${content}"`);
                hasErrors = true;
            }
        }
    }
}

if (hasErrors) {
    process.exit(1);
}
console.log('All .akf files validated successfully');
