import React, { useState } from "react";
import {
    TextField,
    Stack,
    Box,
    Typography,
    Button,
    Switch,
    FormControlLabel,
} from "@mui/material";
import axios from "axios";

export const MapController = () => {
    const [ra, setRa] = useState("0");
    const [dec, setDec] = useState("0");
    const [duration, setDuration] = useState("60");
    const [isTrackMode, setIsTrackMode] = useState(false);

    const handleSubmit = async () => {
        try {
            const payload: { ra: number; dec: number; duration?: number } = {
                ra: Number(ra),
                dec: Number(dec),
            };

            if (isTrackMode) {
                payload.duration = Number(duration);
            }

            const response = await axios.post(isTrackMode ? "/track" : "/point", payload);
            console.log(response.data);
        } catch (error) {
            console.error("Error sending request:", error);
        }
    };

    return (
        <Box display="flex" gap={4}>
            <Stack spacing={2} direction="column">
                <Box display="flex" alignItems="center" gap={1}>
                    <FormControlLabel
                        control={
                            <Switch
                                color="primary"
                                checked={isTrackMode}
                                onChange={(event) => setIsTrackMode(event.target.checked)}
                            />
                        }
                        label={isTrackMode ? "Track mode" : "Point mode"}
                    />
                </Box>
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
                {isTrackMode && (
                    <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body1">Duration (s):</Typography>
                        <TextField
                            type="number"
                            size="small"
                            value={duration}
                            onChange={(e) => setDuration(e.target.value)}
                        />
                    </Box>
                )}

                <Button variant="contained" onClick={handleSubmit}>
                    {isTrackMode ? "Track" : "Point"}
                </Button>
            </Stack>
        </Box>
    );
};