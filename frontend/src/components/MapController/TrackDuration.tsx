import React from 'react';
import { Box, Typography, TextField } from '@mui/material';

type TrackDurationProps = {
    duration: string;
    onChange: (value: string) => void;
};

export const TrackDuration = ({ duration, onChange }: TrackDurationProps) => (
    <Box display='flex' alignItems='center' gap={1}>
        <Typography variant='body1'>Duration (s):</Typography>
        <TextField
            type='number'
            size='small'
            value={duration}
            onChange={(e) => onChange(e.target.value)}
        />
    </Box>
);
