import React, { useEffect, useState } from 'react';
import { Stack, Box, Button } from '@mui/material';
import axios from 'axios';
import { CoordInputs } from './CoordInputs';
import { ModeSwitches } from './ModeSwitches';
import { TrackDuration } from './TrackDuration';

type PointPayload =
    | { ra: number; dec: number; duration?: number }
    | { az: number; alt: number };

type CoordField = 'ra' | 'dec' | 'az' | 'alt';

type Star = {
    name: string;
    ra: number;
    dec: number;
    parallax_mas: number;
};

interface MapControllerProps {
    isTrackMode: boolean;
    onTrackModeChange: (enabled: boolean) => void;
}

const API_BASE_URL = 'https://spex-telescope-backend.online';
const BROWSE_PAGE_SIZE = 100;

export const MapController = ({ isTrackMode, onTrackModeChange }: MapControllerProps) => {
    const [ra, setRa] = useState('0');
    const [dec, setDec] = useState('0');
    const [az, setAz] = useState('0');
    const [alt, setAlt] = useState('0');
    const [coordMode, setCoordMode] = useState<'radec' | 'altaz'>('radec');
    const [browseStars, setBrowseStars] = useState<Star[]>([]);

    const [duration, setDuration] = useState('60');

    const isRaDecMode = coordMode === 'radec';
    useEffect(() => {
        const loadInitialBrowsePage = async () => {
            try {
                const response = await axios.get<{ stars: Star[] }>(`${API_BASE_URL}/stars/page`, {
                    params: {
                        page: 0,
                        page_size: BROWSE_PAGE_SIZE,
                    },
                });
                setBrowseStars(response.data.stars ?? []);
            } catch (error) {
                console.error('Error loading star catalog:', error);
            }
        };

        loadInitialBrowsePage();
    }, []);

    const loadBrowsePage = async (page: number, pageSize: number) => {
        const response = await axios.get<{ stars: Star[] }>(`${API_BASE_URL}/stars/page`, {
            params: { page, page_size: pageSize },
        });
        return response.data.stars ?? [];
    };

    const searchStars = async (query: string, limit = 50) => {
        if (!query.trim()) {
            return [];
        }
        const response = await axios.get<{ stars: Star[] }>(`${API_BASE_URL}/stars/search`, {
            params: { query, limit },
        });
        return response.data.stars ?? [];
    };

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

            const response = await axios.post(
                isTrackMode ? `${API_BASE_URL}/track` : `${API_BASE_URL}/point`,
                payload,
            );
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

    const handleSelectStar = (selectedStar: Star | null) => {
        if (!selectedStar) {
            setRa('');
            setDec('');
            return;
        }

        setRa(selectedStar.ra.toString());
        setDec(selectedStar.dec.toString());
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
                    initialBrowseStars={browseStars}
                    onLoadBrowsePage={loadBrowsePage}
                    onSearchStars={searchStars}
                    onSelectStar={handleSelectStar}
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
