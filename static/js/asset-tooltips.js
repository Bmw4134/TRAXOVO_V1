async function loadTooltipData() {
  try {
    const response = await fetch("/api/fleet/assets");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    let assets = [];
    if (data.assets && Array.isArray(data.assets)) {
      assets = data.assets;
    } else if (Array.isArray(data)) {
      assets = data;
    } else if (data.data && Array.isArray(data.data)) {
      assets = data.data;
    }
    if (assets.length > 0) {
      console.log(`Loaded ${assets.length} authentic assets from GAUGE API`);
      return assets;
    } else {
      console.log("No asset data available from API");
      return [];
    }
  } catch (error) {
    console.error("Failed to load tooltip data:", error);
    return [];
  }
}
