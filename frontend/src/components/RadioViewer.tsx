import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Box, Button, CircularProgress, MenuItem, TextField, Typography } from '@mui/material';

type RadioPayload = {
    status: string;
    error: string | null;
    data: {
        timestamp: number;
        center_freq_hz: number;
        peak_freq_hz: number;
        peak_power_db: number;
        source: string;
        bandwidth_hz: number;
        gain: string | number;
        n_ave: number;
        record_mode: 'instant' | 'average';
        observation_mode: 'spectrum' | 'hotcold';
        integration_count: number;
        bins_hz: number[];
        power_db: number[];
        averaged_power_db: number[];
        calibrated_power_db: number[] | null;
        cold_profile_db: number[] | null;
    } | null;
};

const RADIO_ENDPOINT = 'https://spex-telescope-backend.online/radio';

const formatMhz = (valueHz: number) => (valueHz / 1_000_000).toFixed(6);

export const RadioViewer = () => {
    const [payload, setPayload] = useState<RadioPayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSavingMode, setIsSavingMode] = useState(false);
    const [centerFreqHzInput, setCenterFreqHzInput] = useState('');
    const [bandwidthHzInput, setBandwidthHzInput] = useState('');
    const [gainInput, setGainInput] = useState('');
    const [nAveInput, setNAveInput] = useState('');
    const [activeInput, setActiveInput] = useState<null | 'center_freq_hz' | 'bandwidth_hz' | 'gain' | 'n_ave'>(null);
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
        const values = payload?.data?.calibrated_power_db ?? payload?.data?.averaged_power_db ?? payload?.data?.power_db;
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

    useEffect(() => {
        if (!payload?.data) {
            return;
        }
        if (activeInput !== 'center_freq_hz') {
            setCenterFreqHzInput(String(payload.data.center_freq_hz));
        }
        if (activeInput !== 'bandwidth_hz') {
            setBandwidthHzInput(String(payload.data.bandwidth_hz));
        }
        if (activeInput !== 'gain') {
            setGainInput(String(payload.data.gain));
        }
        if (activeInput !== 'n_ave') {
            setNAveInput(String(payload.data.n_ave));
        }
    }, [payload, activeInput]);

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
    const hasColdProfile = Boolean(data.cold_profile_db);

    const updateMode = async (modePatch: { record_mode?: 'instant' | 'average'; observation_mode?: 'spectrum' | 'hotcold' }) => {
        setIsSavingMode(true);
        try {
            const response = await axios.post<RadioPayload>(`${RADIO_ENDPOINT}/config`, modePatch);
            setPayload(response.data);
        } catch (error) {
            console.error('Failed to update radio mode', error);
        } finally {
            setIsSavingMode(false);
        }
    };

    const updateSignalConfig = async () => {
        const submittedConfig = {
            center_freq_hz: Number(centerFreqHzInput),
            bandwidth_hz: Number(bandwidthHzInput),
            gain: gainInput.trim() || 'auto',
            n_ave: Number(nAveInput),
        };

        setDirtyInputs({
            center_freq_hz: false,
            bandwidth_hz: false,
            gain: false,
            n_ave: false,
        });
        setPendingSignalConfig(submittedConfig);
        setIsSavingMode(true);
        try {
            const response = await axios.post<RadioPayload>(`${RADIO_ENDPOINT}/config`, submittedConfig);
            setPayload(response.data);
        } catch (error) {
            setPendingSignalConfig(null);
            console.error('Failed to update radio signal config', error);
        } finally {
            setIsSavingMode(false);
        }
    };

    const captureCold = async () => {
        setIsSavingMode(true);
        try {
            const response = await axios.post<RadioPayload>(`${RADIO_ENDPOINT}/capture-cold`);
            setPayload(response.data);
        } catch (error) {
            console.error('Failed to capture cold profile', error);
        } finally {
            setIsSavingMode(false);
        }
    };

    return (
        <Box className='radio-viewer'>
            <Typography variant='h6'>Radio Viewer</Typography>
            <Typography variant='body2'>Status: {payload.status}</Typography>
            <Typography variant='body2'>Source: {data.source}</Typography>
            <Typography variant='body2'>Center: {formatMhz(data.center_freq_hz)} MHz</Typography>
            <Typography variant='body2'>Bandwidth: {formatMhz(data.bandwidth_hz)} MHz</Typography>
            <Typography variant='body2'>Gain: {data.gain}</Typography>
            <Typography variant='body2'>N_Ave: {data.n_ave}</Typography>
            <Typography variant='body2'>Peak: {formatMhz(data.peak_freq_hz)} MHz @ {data.peak_power_db.toFixed(2)} dB</Typography>
            <Typography variant='body2'>Integrated frames: {data.integration_count}</Typography>

            <Box display='flex' gap={1} mt={1} mb={1} flexWrap='wrap'>
                <TextField
                    select
                    size='small'
                    label='Record'
                    value={data.record_mode}
                    disabled={isSavingMode}
                    onChange={(e) => updateMode({ record_mode: e.target.value as 'instant' | 'average' })}
                >
                    <MenuItem value='average'>Average</MenuItem>
                    <MenuItem value='instant'>Instant</MenuItem>
                </TextField>
                <TextField
                    select
                    size='small'
                    label='Observation'
                    value={data.observation_mode}
                    disabled={isSavingMode}
                    onChange={(e) => updateMode({ observation_mode: e.target.value as 'spectrum' | 'hotcold' })}
                >
                    <MenuItem value='spectrum'>Spectrum</MenuItem>
                    <MenuItem value='hotcold'>Hot/Cold</MenuItem>
                </TextField>
                <Button variant='outlined' size='small' disabled={isSavingMode} onClick={captureCold}>
                    Save Cold Profile
                </Button>
            </Box>
            <Box display='flex' gap={1} mt={1} mb={1} flexWrap='wrap'>
                <TextField
                    size='small'
                    label='Center Freq (Hz)'
                    value={centerFreqHzInput}
                    disabled={isSavingMode}
                    onChange={(e) => setCenterFreqHzInput(e.target.value)}
                    onFocus={() => setActiveInput('center_freq_hz')}
                    onBlur={() => setActiveInput(null)}
                />
                <TextField
                    select
                    size='small'
                    label='Bandwidth (Hz)'
                    value={bandwidthHzInput}
                    disabled={isSavingMode}
                    onChange={(e) => setBandwidthHzInput(e.target.value)}
                    onFocus={() => setActiveInput('bandwidth_hz')}
                    onBlur={() => setActiveInput(null)}
                >
                    <MenuItem value='1024000'>1024000</MenuItem>
                    <MenuItem value='2400000'>2400000</MenuItem>
                </TextField>
                <TextField
                    size='small'
                    label='Gain (auto or dB)'
                    value={gainInput}
                    disabled={isSavingMode}
                    onChange={(e) => setGainInput(e.target.value)}
                    onFocus={() => setActiveInput('gain')}
                    onBlur={() => setActiveInput(null)}
                />
                <TextField
                    size='small'
                    label='N_Ave'
                    value={nAveInput}
                    disabled={isSavingMode}
                    onChange={(e) => setNAveInput(e.target.value)}
                    onFocus={() => setActiveInput('n_ave')}
                    onBlur={() => setActiveInput(null)}
                />
                <Button variant='outlined' size='small' disabled={isSavingMode} onClick={updateSignalConfig}>
                    Save Signal Config
                </Button>
            </Box>
            {data.observation_mode === 'hotcold' && !hasColdProfile && (
                <Typography variant='caption' display='block'>
                    No cold profile saved yet; click "Save Cold Profile" while pointed at cold sky.
                </Typography>
            )}

            <svg viewBox='0 0 100 100' preserveAspectRatio='none' className='radio-chart'>
                <polyline fill='none' stroke='currentColor' strokeWidth='1.4' points={points} />
            </svg>

            <Typography variant='caption' display='block'>
                Last update: {new Date(data.timestamp * 1000).toLocaleTimeString()}
            </Typography>
        </Box>
    );
};
