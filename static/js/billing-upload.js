/*
TRAXOVO Billing Upload Handler
Integrates with unified deduplication processor
*/

async function uploadAndTrigger(file, tableName) {
  try {
    // Create form data for file upload
    const formData = new FormData();
    formData.append("file", file);

    // Upload file first
    const uploadResponse = await fetch("/api/upload-file", {
      method: "POST",
      body: formData,
    });

    if (!uploadResponse.ok) {
      throw new Error("File upload failed");
    }

    const uploadResult = await uploadResponse.json();

    // Trigger processing with deduplication
    const processResponse = await fetch(
      `/api/process-upload?file=${file.name}&table=${tableName || "billing_records"}`,
    );
    const processResult = await processResponse.json();

    if (processResult.error) {
      throw new Error(processResult.error);
    }

    // Display results
    const message = `Processing complete: ${processResult.inserted} records inserted, ${processResult.skipped} duplicates skipped, ${processResult.flagged} similar records flagged`;

    // Update UI with results
    if (document.getElementById("upload-results")) {
      document.getElementById("upload-results").innerHTML = `
                <div class="alert alert-success">
                    <h5>Upload Successful</h5>
                    <p>${message}</p>
                    <ul>
                        <li>Total processed: ${processResult.total_processed}</li>
                        <li>New records: ${processResult.inserted}</li>
                        <li>Duplicates skipped: ${processResult.skipped}</li>
                        <li>Similar records flagged: ${processResult.flagged}</li>
                    </ul>
                </div>
            `;
    } else {
      alert(message);
    }

    return processResult;
  } catch (error) {
    console.error("Upload error:", error);
    const errorMessage = `Upload failed: ${error.message}`;

    if (document.getElementById("upload-results")) {
      document.getElementById("upload-results").innerHTML = `
                <div class="alert alert-danger">
                    <h5>Upload Failed</h5>
                    <p>${errorMessage}</p>
                </div>
            `;
    } else {
      alert(errorMessage);
    }

    return { error: error.message };
  }
}

// Initialize file upload handlers
document.addEventListener("DOMContentLoaded", function () {
  const fileInputs = document.querySelectorAll('input[type="file"]');

  fileInputs.forEach((input) => {
    input.addEventListener("change", function (event) {
      const file = event.target.files[0];
      if (file) {
        const tableName = input.dataset.table || "billing_records";
        uploadAndTrigger(file, tableName);
      }
    });
  });
});
