import React, { useState } from 'react';
import {
    TextField,
    Stack,
    Box,
    Typography,
    Button,
    Switch,
    FormControlLabel,
} from '@mui/material';
import axios from 'axios';
import { CoordRow } from './CoordRow';

type PointPayload =
    | { ra: number; dec: number; duration?: number }
    | { az: number; alt: number };

type CoordField = 'ra' | 'dec' | 'az' | 'alt';


export const MapController = () => {
    const [ra, setRa] = useState('0');
    const [dec, setDec] = useState('0');
    const [az, setAz] = useState('0');
    const [alt, setAlt] = useState('0');
    const [coordMode, setCoordMode] = useState<'radec' | 'altaz'>('radec');

    const [duration, setDuration] = useState('60');
    const [isTrackMode, setIsTrackMode] = useState(false);

    const handleSubmit = async () => {
        try {
            var payload: PointPayload =
                coordMode === 'radec'
                    ? { ra: Number(ra), dec: Number(dec) }
                    : { az: Number(az), alt: Number(alt) };


            if (isTrackMode) {
                if (coordMode !== 'radec') {
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
                    duration: parsedDuration
                }
            }


            const response = await axios.post(isTrackMode ? '/track' : '/point', payload);
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
                console.error('Error setting field: field must be ra, dec, alt, or az')
        }
    }

    const toggleCoordMode = () => {
        coordMode === 'radec' ? setCoordMode('altaz') : setCoordMode('radec');
    }

    return (
        <Box display='flex' gap={4}>
            <Stack spacing={2} direction='column'>
                <Stack direction='column' spacing={1} alignItems='left'>
                    <Stack spacing={0.5} alignItems="flex-start">
                        <Stack direction="row" spacing={1} alignItems="center">
                            <Typography>Point</Typography>
                            <Switch
                                color="primary"
                                checked={isTrackMode}
                                onChange={(event) => setIsTrackMode(event.target.checked)}
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
                                onChange={toggleCoordMode}
                            />
                            <Typography>Alt/Az</Typography>
                        </Stack>
                    </Stack>
                </Stack>
                {coordMode === 'radec' ? (
                    <>
                        <CoordRow
                            label="RA"
                            value={ra}
                            onChange={(v) => handleChangeCoordinate('ra', v)}
                        />
                        <CoordRow
                            label="Dec"
                            value={dec}
                            onChange={(v) => handleChangeCoordinate('dec', v)}
                        />
                    </>
                ) : (
                    <>
                        <CoordRow
                            label="Alt"
                            value={alt}
                            onChange={(v) => handleChangeCoordinate('alt', v)}
                        />
                        <CoordRow
                            label="Az"
                            value={az}
                            onChange={(v) => handleChangeCoordinate('az', v)}
                        />
                    </>
                )}
                {isTrackMode && coordMode === 'radec' && (
                    <Box display='flex' alignItems='center' gap={1}>
                        <Typography variant='body1'>Duration (s):</Typography>
                        <TextField
                            type='number'
                            size='small'
                            value={duration}
                            onChange={(e) => setDuration(e.target.value)}
                        />
                    </Box>
                )}

                <Button variant='contained' onClick={handleSubmit}>
                    {isTrackMode ? 'Track' : 'Point'}
                </Button>
            </Stack>
        </Box>
    );
};