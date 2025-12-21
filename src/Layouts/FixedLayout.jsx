// src/layouts/FixedLayout.jsx
import React from "react";
import { Box } from "@mui/material";

export default function FixedLayout({ children }) {
  return (
    <Box
      sx={{
        width: "100%",        // 화면 폭에 맞춤
        maxWidth: "1920px",   // 최대 해상도 제한 (예: FHD)
        minWidth: "100%",   // 너무 좁아지지 않도록 최소 폭
        mx: "auto",
        minHeight: "100vh",
        px: 0,
      }}
    >
      {children}
    </Box>
  );
}
