import { useEffect, useMemo, useRef, useState } from 'react';
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

type ScanPixel = {
    x: number;
    y: number;
    value: number;
};

const RADIO_ENDPOINT = 'https://spex-telescope-backend.online/radio';
const GRID_SIZE = 24;

const formatMhz = (valueHz: number) => (valueHz / 1_000_000).toFixed(6);

const normalizeDb = (value: number, min = -120, max = -10) => {
    const clamped = Math.max(min, Math.min(max, value));
    return (clamped - min) / (max - min);
};

const buildInitialMap = () => Array.from({ length: GRID_SIZE }, () => Array.from({ length: GRID_SIZE }, () => 0));

const valueToColor = (value: number) => {
    const hue = 240 - value * 240;
    const lightness = 26 + value * 48;
    return `hsl(${hue} 85% ${lightness}%)`;
};

interface RadioViewerProps {
    isTrackMode: boolean;
}

export const RadioViewer = ({ isTrackMode }: RadioViewerProps) => {
    const [payload, setPayload] = useState<RadioPayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSavingMode, setIsSavingMode] = useState(false);
    const [centerFreqHzInput, setCenterFreqHzInput] = useState('');
    const [bandwidthHzInput, setBandwidthHzInput] = useState('');
    const [gainInput, setGainInput] = useState('');
    const [nAveInput, setNAveInput] = useState('');
    const [isScanEnabled, setIsScanEnabled] = useState(false);
    const [scanMap, setScanMap] = useState<number[][]>(() => buildInitialMap());
    const [currentPixel, setCurrentPixel] = useState<ScanPixel | null>(null);
    const cursorRef = useRef({ x: 0, y: 0, direction: 1 });

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

    useEffect(() => {
        if (isTrackMode) {
            setIsScanEnabled(true);
        }
    }, [isTrackMode]);

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
        setCenterFreqHzInput(String(payload.data.center_freq_hz));
        setBandwidthHzInput(String(payload.data.bandwidth_hz));
        setGainInput(String(payload.data.gain));
        setNAveInput(String(payload.data.n_ave));
    }, [payload]);

    useEffect(() => {
        if (!isScanEnabled || !payload?.data) {
            return;
        }

        const value = normalizeDb(payload.data.peak_power_db);
        const { x, y } = cursorRef.current;

        setScanMap((previousMap) => {
            const nextMap = previousMap.map((row) => [...row]);
            nextMap[y][x] = value;
            return nextMap;
        });
        setCurrentPixel({ x, y, value });

        const cursor = cursorRef.current;
        const nextX = cursor.x + cursor.direction;

        if (nextX >= GRID_SIZE || nextX < 0) {
            cursor.y = (cursor.y + 1) % GRID_SIZE;
            cursor.direction *= -1;
        } else {
            cursor.x = nextX;
        }
    }, [payload, isScanEnabled]);

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
        setIsSavingMode(true);
        try {
            const response = await axios.post<RadioPayload>(`${RADIO_ENDPOINT}/config`, {
                center_freq_hz: Number(centerFreqHzInput),
                bandwidth_hz: Number(bandwidthHzInput),
                gain: gainInput.trim() || 'auto',
                n_ave: Number(nAveInput),
            });
            setPayload(response.data);
        } catch (error) {
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

    const resetScan = () => {
        setScanMap(buildInitialMap());
        setCurrentPixel(null);
        cursorRef.current = { x: 0, y: 0, direction: 1 };
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
                />
                <TextField
                    select
                    size='small'
                    label='Bandwidth (Hz)'
                    value={bandwidthHzInput}
                    disabled={isSavingMode}
                    onChange={(e) => setBandwidthHzInput(e.target.value)}
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
                />
                <TextField
                    size='small'
                    label='N_Ave'
                    value={nAveInput}
                    disabled={isSavingMode}
                    onChange={(e) => setNAveInput(e.target.value)}
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

            <Box className='hydrogen-map-panel'>
                <Box display='flex' alignItems='center' justifyContent='space-between' mb={1}>
                    <Typography variant='subtitle2'>Hydrogen Scan Map (prototype)</Typography>
                    <Box display='flex' gap={1}>
                        <Button size='small' variant='outlined' onClick={() => setIsScanEnabled((current) => !current)}>
                            {isScanEnabled ? 'Pause scan' : 'Resume scan'}
                        </Button>
                        <Button size='small' variant='outlined' onClick={resetScan}>
                            Reset
                        </Button>
                    </Box>
                </Box>

                {isTrackMode && currentPixel ? (
                    <Typography variant='caption' display='block' mb={1}>
                        Current pixel x={currentPixel.x}, y={currentPixel.y}, normalized HI={currentPixel.value.toFixed(3)}
                    </Typography>
                ) : (
                    <Typography variant='caption' display='block' mb={1}>
                        Track mode off: showing artistic sky preview while idle.
                    </Typography>
                )}

                {isTrackMode ? (
                    <Box className='hydrogen-grid' role='img' aria-label='Hydrogen density map'>
                        {scanMap.map((row, y) =>
                            row.map((value, x) => {
                                const isCurrent = currentPixel?.x === x && currentPixel?.y === y;
                                return (
                                    <Box
                                        key={`${x}-${y}`}
                                        className={`hydrogen-cell ${isCurrent ? 'is-current' : ''}`}
                                        style={{ backgroundColor: valueToColor(value) }}
                                    />
                                );
                            })
                        )}
                    </Box>
                ) : (
                    <Box className='hydrogen-art' role='img' aria-label='Stylized sky background when not tracking'>
                        <span className='star star-a' />
                        <span className='star star-b' />
                        <span className='star star-c' />
                        <span className='star star-d' />
                    </Box>
                )}
            </Box>

            <Typography variant='caption' display='block'>
                Last update: {new Date(data.timestamp * 1000).toLocaleTimeString()}
            </Typography>
        </Box>
    );
};
