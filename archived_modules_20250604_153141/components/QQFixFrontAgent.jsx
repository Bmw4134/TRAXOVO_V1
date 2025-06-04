// QQFixFrontAgent.jsx
import { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function QQFixFrontAgent() {
  const [fixes, setFixes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/qq_fix_plan.json")
      .then((res) => res.json())
      .then((data) => {
        setFixes(data);
        setLoading(false);
      });
  }, []);

  const handleFix = (filePath) => {
    fetch("/api/qq/patch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file: filePath })
    }).then((res) => res.json())
      .then((data) => alert(data.message || "Patched."));
  };

  if (loading) return <p className="p-4 text-white">Loading fix plan...</p>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      {fixes.map((fix, index) => (
        <Card key={index} className="bg-zinc-900 text-white">
          <CardContent className="space-y-2">
            <p className="text-xs text-zinc-400">{fix.file}</p>
            <p className="text-sm">{fix.reason}</p>
            <p className="text-xs italic">{fix.recommended_action}</p>
            <Button className="mt-2" onClick={() => handleFix(fix.file)}>Apply Fix</Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}