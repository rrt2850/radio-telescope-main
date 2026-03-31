import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Box, CircularProgress, Typography } from '@mui/material';

type RadioPayload = {
    status: string;
    error: string | null;
    data: {
        timestamp: number;
        center_freq_hz: number;
        peak_freq_hz: number;
        peak_power_db: number;
        source: string;
        bins_hz: number[];
        power_db: number[];
    } | null;
};

const RADIO_ENDPOINT = 'https://spex-telescope-backend.online/radio';

const formatMhz = (valueHz: number) => (valueHz / 1_000_000).toFixed(6);

export const RadioViewer = () => {
    const [payload, setPayload] = useState<RadioPayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        const fetchRadio = async () => {
            try {
                const response = await axios.get<RadioPayload>(RADIO_ENDPOINT);
                if (isMounted) {
                    setPayload(response.data);
                    setIsLoading(false);
                }
            } catch (error) {
                if (isMounted) {
                    setPayload({ status: 'error', error: 'Unable to reach radio endpoint.', data: null });
                    setIsLoading(false);
                }
                console.error('Error fetching radio data:', error);
            }
        };

        fetchRadio();
        const intervalId = window.setInterval(fetchRadio, 2000);

        return () => {
            isMounted = false;
            window.clearInterval(intervalId);
        };
    }, []);

    const points = useMemo(() => {
        const values = payload?.data?.power_db;
        if (!values || values.length === 0) {
            return '';
        }

        const min = Math.min(...values);
        const max = Math.max(...values);
        const span = max - min || 1;

        return values
            .map((value, index) => {
                const x = (index / (values.length - 1)) * 100;
                const normalizedY = (value - min) / span;
                const y = 100 - normalizedY * 100;
                return `${x},${y}`;
            })
            .join(' ');
    }, [payload]);

    if (isLoading) {
        return (
            <Box className='radio-viewer'>
                <Typography variant='h6'>Radio Viewer</Typography>
                <CircularProgress size={24} />
            </Box>
        );
    }

    if (!payload?.data) {
        return (
            <Box className='radio-viewer'>
                <Typography variant='h6'>Radio Viewer</Typography>
                <Typography variant='body2'>
                    No radio data is being received right now. {payload?.error ? `(${payload.error})` : ''}
                </Typography>
            </Box>
        );
    }

    const { data } = payload;

    return (
        <Box className='radio-viewer'>
            <Typography variant='h6'>Radio Viewer</Typography>
            <Typography variant='body2'>Status: {payload.status}</Typography>
            <Typography variant='body2'>Source: {data.source}</Typography>
            <Typography variant='body2'>Center: {formatMhz(data.center_freq_hz)} MHz</Typography>
            <Typography variant='body2'>Peak: {formatMhz(data.peak_freq_hz)} MHz @ {data.peak_power_db.toFixed(2)} dB</Typography>

            <svg viewBox='0 0 100 100' preserveAspectRatio='none' className='radio-chart'>
                <polyline fill='none' stroke='currentColor' strokeWidth='1.4' points={points} />
            </svg>

            <Typography variant='caption' display='block'>
                Last update: {new Date(data.timestamp * 1000).toLocaleTimeString()}
            </Typography>
        </Box>
    );
};
