import React from "react";

export const Watermark: React.FC<{ text?: string; color?: string }> = ({
  text = "ZkAGI", color = "rgba(124,58,237,0.25)",
}) => (
  <div style={{ position: "absolute", top: 24, right: 32 }}>
    <span style={{ color, fontSize: 20, fontWeight: 800, fontFamily: "'Inter', sans-serif", letterSpacing: 2, textTransform: "uppercase" }}>
      {text}
    </span>
  </div>
);
