
async function uploadAndTrigger(file, tableName) {
  const { data, error } = await supabase
    .storage
    .from('equipment-billings')
    .upload(`uploads/${file.name}`, file, { upsert: true });

  if (error) return console.error("Upload error:", error);

  const trigger = await fetch(`/api/process-upload?file=${file.name}&table=${tableName}`);
  const result = await trigger.json();
  alert(result.message);
}
