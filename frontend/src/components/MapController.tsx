
import React, { useState } from "react";
import { StarMap } from "./StarMap";
import { TextField, Stack, Box, Typography } from "@mui/material";
import Button from '@mui/material/Button';
import axios from 'axios';


export const MapController = () => {
    const [ra, setRa] = useState("0");
    const [dec, setDec] = useState("0");
    const [fov, setFov] = useState("90");

    const handleSubmit = async () => {
        try {
            const response = await axios.post(
                'https://spex-telescope-backend.online/point',
                {
                    ra: Number(ra),
                    dec: Number(dec)
                }
            );
            console.log(response.data);
        } catch (error) {
            console.error('Error sending POST request:', error);
        }
    };





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

                <Button variant="contained" onClick={handleSubmit}>
                    Submit
                </Button>
            </Stack>
        </Box>
    );
};