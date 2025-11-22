
import React, { useState } from "react";
import { StarMap } from "./StarMap";
import { TextField, Stack, Box, Typography } from "@mui/material";

export const MapController = () => {
    const [ra, setRa] = useState("0");
    const [dec, setDec] = useState("0");
    const [fov, setFov] = useState("90");

    const onChange = (newRa: string, newDec: string, newFov: string) => {
        setRa(newRa);
        setDec(newDec);
        setFov(newFov);
    }

    return (
        <Box display="flex" gap={4}>
            <Stack spacing={2} direction="column">
                <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">RA:</Typography>
                    <TextField
                        type="number"
                        size="small"
                        value={ra}
                        onChange={(e) => setRa(e.target.value)}
                    />
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">Dec:</Typography>
                    <TextField
                        type="number"
                        size="small"
                        value={dec}
                        onChange={(e) => setDec(e.target.value)}
                    />
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">FOV:</Typography>
                    <TextField
                        type="number"
                        size="small"
                        value={fov}
                        onChange={(e) => setFov(e.target.value)}
                    />
                </Box>
            </Stack>
        </Box>
    );
};