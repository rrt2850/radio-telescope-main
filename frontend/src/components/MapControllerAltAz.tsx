
import React, { useState } from "react";
import { StarMap } from "./StarMap";
import { TextField, Stack, Box, Typography } from "@mui/material";
import Button from '@mui/material/Button';
import axios from 'axios';


export const MapControllerAltAz = () => {
    const [alt, setAlt] = useState("0");
    const [az, setAz] = useState("0");

    const handleSubmit = async () => {
        try {
            const response = await axios.post(
                'https://spex-telescope-backend.online/point',
                {
                    alt: Number(alt),
                    az: Number(az)
                }
            );
            console.log(response.data);
        } catch (error) {
            console.error('Error sending POST request:', error);
        }
    };

    return (
        <Box display="flex" gap={4}>
            <Stack spacing={2} direction="column">
                <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">Alt:</Typography>
                    <TextField
                        type="number"
                        size="small"
                        value={alt}
                        onChange={(e) => setAlt(e.target.value)}
                    />
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">Az:</Typography>
                    <TextField
                        type="number"
                        size="small"
                        value={az}
                        onChange={(e) => setAz(e.target.value)}
                    />
                </Box>

                <Button variant="contained" onClick={handleSubmit}>
                    Submit
                </Button>
            </Stack>
        </Box>
    );
};