import React, { useState } from 'react';
import { Stack, Box, Button } from '@mui/material';
import axios from 'axios';
import { CoordInputs } from './CoordInputs';
import { ModeSwitches } from './ModeSwitches';
import { TrackDuration } from './TrackDuration';

type PointPayload =
    | { ra: number; dec: number; duration?: number }
    | { az: number; alt: number };

type CoordField = 'ra' | 'dec' | 'az' | 'alt';

interface MapControllerProps {
    isTrackMode: boolean;
    onTrackModeChange: (enabled: boolean) => void;
}

export const MapController = ({ isTrackMode, onTrackModeChange }: MapControllerProps) => {
    const [ra, setRa] = useState('0');
    const [dec, setDec] = useState('0');
    const [az, setAz] = useState('0');
    const [alt, setAlt] = useState('0');
    const [coordMode, setCoordMode] = useState<'radec' | 'altaz'>('radec');

    const [duration, setDuration] = useState('60');

    const isRaDecMode = coordMode === 'radec';

    const buildPayload = () =>
        isRaDecMode
            ? { ra: Number(ra), dec: Number(dec) }
            : { az: Number(az), alt: Number(alt) };

    const handleSubmit = async () => {
        try {
            let payload: PointPayload = buildPayload();

            if (isTrackMode) {
                if (!isRaDecMode) {
                    alert('To track, you must use RA/Dec coordinates :(');
                    return;
                }

                const parsedDuration = Number(duration);
                if (isNaN(parsedDuration) || parsedDuration <= 0) {
                    alert('Duration must be a positive number.');
                    return;
                }

                payload = {
                    ...payload,
                    duration: parsedDuration,
                };
            }

            const response = await axios.post(isTrackMode ? 'https://spex-telescope-backend.online/track' : 'https://spex-telescope-backend.online/point', payload);
            console.log(response.data);
        } catch (error) {
            console.error('Error sending request:', error);
        }
    };

    const handleChangeCoordinate = (field: CoordField, value: string) => {
        switch (field) {
            case 'ra':
                setRa(value);
                break;
            case 'dec':
                setDec(value);
                break;
            case 'alt':
                setAlt(value);
                break;
            case 'az':
                setAz(value);
                break;
            default:
                console.error('Error setting field: field must be ra, dec, alt, or az');
        }
    };

    const toggleCoordMode = () => {
        coordMode === 'radec' ? setCoordMode('altaz') : setCoordMode('radec');
    };

    return (
        <Box display='flex' gap={4}>
            <Stack spacing={2} direction='column'>
                <ModeSwitches
                    isTrackMode={isTrackMode}
                    coordMode={coordMode}
                    onToggleTrack={onTrackModeChange}
                    onToggleCoordMode={toggleCoordMode}
                />
                <CoordInputs
                    coordMode={coordMode}
                    ra={ra}
                    dec={dec}
                    alt={alt}
                    az={az}
                    onChange={handleChangeCoordinate}
                />
                {isTrackMode && isRaDecMode && (
                    <TrackDuration
                        duration={duration}
                        onChange={(value) => setDuration(value)}
                    />
                )}

                <Button variant='contained' onClick={handleSubmit}>
                    {isTrackMode ? 'Track' : 'Point'}
                </Button>
            </Stack>
        </Box>
    );
};
