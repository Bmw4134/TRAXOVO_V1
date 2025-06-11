/**
 * TRAXOVO ∞ Clarity Core - Asset Parser Utilities
 * Enhanced asset metadata parsing for enterprise fleet management
 */

function parseAssetMeta(assetId) {
    if (!assetId) return { driverName: "", rawId: "" };

    const matchParentheses = assetId.match(/\((.*?)\)/);
    const matchDash = assetId.split(" - ");

    const driverName = matchDash.length > 1
        ? matchDash[1].trim()
        : matchParentheses
        ? matchParentheses[1].trim()
        : assetId.trim();

    const rawId = matchDash[0].replace(/[^0-9]/g, "").trim();
    return { driverName, rawId };
}

/**
 * Enhanced asset metadata extractor with additional parsing capabilities
 */
function parseEnhancedAssetMeta(assetId) {
    const basicMeta = parseAssetMeta(assetId);
    
    // Extract additional metadata patterns
    const patterns = {
        // Equipment type patterns (MT = Motor Grader, DT = Dump Truck, etc.)
        equipmentType: assetId.match(/^([A-Z]{2,3})-?\d+/),
        
        // Department/Division codes
        departmentCode: assetId.match(/\[([A-Z]{2,4})\]/),
        
        // Location indicators
        locationCode: assetId.match(/@([A-Z0-9]+)/),
        
        // Status indicators
        statusCode: assetId.match(/\{([A-Z]+)\}/),
        
        // Project codes
        projectCode: assetId.match(/\#([A-Z0-9-]+)/),
        
        // Vehicle identification number patterns
        vinPattern: assetId.match(/VIN:([A-Z0-9]{17})/i)
    };
    
    return {
        ...basicMeta,
        equipmentType: patterns.equipmentType ? patterns.equipmentType[1] : null,
        departmentCode: patterns.departmentCode ? patterns.departmentCode[1] : null,
        locationCode: patterns.locationCode ? patterns.locationCode[1] : null,
        statusCode: patterns.statusCode ? patterns.statusCode[1] : null,
        projectCode: patterns.projectCode ? patterns.projectCode[1] : null,
        vin: patterns.vinPattern ? patterns.vinPattern[1] : null,
        originalAssetId: assetId
    };
}

/**
 * Generate human-readable asset description
 */
function getAssetDescription(assetMeta) {
    const parts = [];
    
    if (assetMeta.equipmentType) {
        const equipmentTypes = {
            'MT': 'Motor Grader',
            'DT': 'Dump Truck',
            'EX': 'Excavator',
            'BH': 'Backhoe',
            'CR': 'Crane',
            'LD': 'Loader',
            'BZ': 'Bulldozer',
            'SK': 'Skid Steer',
            'TR': 'Truck',
            'TL': 'Tractor-Trailer'
        };
        parts.push(equipmentTypes[assetMeta.equipmentType] || assetMeta.equipmentType);
    }
    
    if (assetMeta.rawId) {
        parts.push(`#${assetMeta.rawId}`);
    }
    
    if (assetMeta.driverName) {
        parts.push(`operated by ${assetMeta.driverName}`);
    }
    
    if (assetMeta.locationCode) {
        parts.push(`at location ${assetMeta.locationCode}`);
    }
    
    return parts.join(' ');
}

/**
 * Batch process multiple asset IDs
 */
function batchParseAssets(assetIds) {
    return assetIds.map(assetId => ({
        original: assetId,
        parsed: parseEnhancedAssetMeta(assetId),
        description: getAssetDescription(parseEnhancedAssetMeta(assetId))
    }));
}

/**
 * Asset validation utilities
 */
function validateAssetId(assetId) {
    if (!assetId || typeof assetId !== 'string') {
        return { valid: false, error: 'Asset ID must be a non-empty string' };
    }
    
    const minLength = 3;
    const maxLength = 100;
    
    if (assetId.length < minLength) {
        return { valid: false, error: `Asset ID must be at least ${minLength} characters` };
    }
    
    if (assetId.length > maxLength) {
        return { valid: false, error: `Asset ID must be no more than ${maxLength} characters` };
    }
    
    // Check for required numeric component
    if (!/\d/.test(assetId)) {
        return { valid: false, error: 'Asset ID must contain at least one numeric digit' };
    }
    
    return { valid: true };
}

/**
 * Generate asset suggestions based on partial input
 */
function generateAssetSuggestions(partialId, knownAssets = []) {
    if (!partialId || partialId.length < 2) return [];
    
    const suggestions = knownAssets.filter(asset => 
        asset.toLowerCase().includes(partialId.toLowerCase())
    );
    
    // Add pattern-based suggestions
    const patterns = [
        `MT-${partialId}`,
        `DT-${partialId}`,
        `EX-${partialId}`,
        `#${partialId} - OPERATOR NAME`
    ];
    
    return [...suggestions, ...patterns].slice(0, 10);
}

// Test data for demonstration
const testAssets = [
    "#210013 - MATTHEW C. SHAYLOR",
    "EX-210013 - MATTHEW C. SHAYLOR",
    "DT-08 - MARIA RODRIGUEZ", 
    "BH-16 - DAVID CHEN",
    "EX-12 - SARAH JOHNSON",
    "CR-23 - MICHAEL BROWN",
    "LD-19 - LISA GARCIA",
    "MT-05 [RD] @FTW {ACTIVE} #2019-044",
    "Asset 100 (John Smith)",
    "Vehicle #500 - Jane Doe @DFW"
];

// Command line execution
if (require.main === module) {
    console.log('TRAXOVO ∞ Clarity Core - Asset Parser Utilities');
    console.log('='.repeat(50));
    
    console.log('\n1. Basic Asset Parsing:');
    testAssets.forEach(asset => {
        const parsed = parseAssetMeta(asset);
        console.log(`Input: ${asset}`);
        console.log(`  Driver: ${parsed.driverName || 'N/A'}`);
        console.log(`  Raw ID: ${parsed.rawId || 'N/A'}`);
        console.log();
    });
    
    console.log('\n2. Enhanced Asset Parsing:');
    testAssets.slice(6, 9).forEach(asset => {
        const enhanced = parseEnhancedAssetMeta(asset);
        console.log(`Input: ${asset}`);
        console.log(`  Enhanced data:`, JSON.stringify(enhanced, null, 2));
        console.log(`  Description: ${getAssetDescription(enhanced)}`);
        console.log();
    });
    
    console.log('\n3. Batch Processing:');
    const batchResults = batchParseAssets(testAssets.slice(0, 3));
    batchResults.forEach(result => {
        console.log(`${result.original} → ${result.description}`);
    });
    
    console.log('\n4. Asset Validation:');
    const testValidation = ['', 'MT', 'MT-07 - JAMES WILSON', 'A'.repeat(150)];
    testValidation.forEach(test => {
        const validation = validateAssetId(test);
        console.log(`"${test}" → ${validation.valid ? 'VALID' : 'INVALID: ' + validation.error}`);
    });
    
    console.log('\n5. Asset Suggestions:');
    const suggestions = generateAssetSuggestions('MT', testAssets);
    console.log('Suggestions for "MT":', suggestions);
    
    console.log('\n✓ Asset parser utilities tested successfully');
}

// Export functions for use in other modules
module.exports = {
    parseAssetMeta,
    parseEnhancedAssetMeta,
    getAssetDescription,
    batchParseAssets,
    validateAssetId,
    generateAssetSuggestions
};