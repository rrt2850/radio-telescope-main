import React from 'react';
import { Stack, Typography, Switch } from '@mui/material';

type ModeSwitchesProps = {
    isTrackMode: boolean;
    coordMode: 'radec' | 'altaz';
    onToggleTrack: (checked: boolean) => void;
    onToggleCoordMode: () => void;
};

export const ModeSwitches = ({
    isTrackMode,
    coordMode,
    onToggleTrack,
    onToggleCoordMode,
}: ModeSwitchesProps) => (
    <Stack direction='column' spacing={1} alignItems='left'>
        <Stack spacing={0.5} alignItems="flex-start">
            <Stack direction="row" spacing={1} alignItems="center">
                <Typography>Point</Typography>
                <Switch
                    color="primary"
                    checked={isTrackMode}
                    onChange={(event) => onToggleTrack(event.target.checked)}
                />
                <Typography>Track</Typography>
            </Stack>
        </Stack>
        <Stack spacing={0.5} alignItems="flex-start">
            <Stack direction="row" spacing={1} alignItems="center">
                <Typography>RA/Dec</Typography>
                <Switch
                    color="primary"
                    checked={coordMode === 'altaz'}
                    onChange={onToggleCoordMode}
                />
                <Typography>Alt/Az</Typography>
            </Stack>
        </Stack>
    </Stack>
);
