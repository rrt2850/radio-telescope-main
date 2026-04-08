import { MouseEvent, useEffect, useMemo, useState } from 'react';
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
const CHART_VIEWBOX_SIZE = 100;
const CHART_HEIGHT_PX = 280;
const TREND_WINDOW_RATIO = 0.035;
const TREND_WINDOW_MIN = 7;
const TREND_WINDOW_MAX = 61;

const getRollingWindowSize = (length: number) => {
    if (length <= 1) {
        return 1;
    }

    const ratioWindow = Math.round(length * TREND_WINDOW_RATIO);
    const bounded = Math.min(TREND_WINDOW_MAX, Math.max(TREND_WINDOW_MIN, ratioWindow));
    return bounded % 2 === 0 ? bounded + 1 : bounded;
};

export const RadioViewer = () => {
    const [payload, setPayload] = useState<RadioPayload | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSavingMode, setIsSavingMode] = useState(false);
    const [centerFreqHzInput, setCenterFreqHzInput] = useState('');
    const [bandwidthHzInput, setBandwidthHzInput] = useState('');
    const [gainInput, setGainInput] = useState('');
    const [nAveInput, setNAveInput] = useState('');
    const [isEditingSignalConfig, setIsEditingSignalConfig] = useState(false);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
    const [selectedSeries, setSelectedSeries] = useState<'spectrum' | 'average' | 'median'>('spectrum');
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

    const chartData = useMemo(() => {
        const values = payload?.data?.calibrated_power_db ?? payload?.data?.averaged_power_db ?? payload?.data?.power_db;
        if (!values || values.length === 0) {
            return {
                points: '',
                averageTrendPoints: '',
                medianTrendPoints: '',
                min: 0,
                max: 1,
                mean: 0,
                median: 0,
                averageY: 50,
                medianY: 50,
                pointData: [] as {
                    x: number;
                    y: number;
                    powerDb: number;
                    freqHz: number;
                    averageTrendDb: number;
                    medianTrendDb: number;
                    averageTrendY: number;
                    medianTrendY: number;
                }[],
            };
        }

        const binsHz = payload?.data?.bins_hz ?? [];
        const fallbackStartHz = (payload?.data?.center_freq_hz ?? 0) - (payload?.data?.bandwidth_hz ?? 0) / 2;
        const fallbackStepHz = values.length > 1 ? (payload?.data?.bandwidth_hz ?? 0) / (values.length - 1) : 0;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const span = max - min || 1;
        const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
        const sortedValues = [...values].sort((a, b) => a - b);
        const median =
            sortedValues.length % 2 === 0
                ? (sortedValues[sortedValues.length / 2 - 1] + sortedValues[sortedValues.length / 2]) / 2
                : sortedValues[Math.floor(sortedValues.length / 2)];
        const trendWindowSize = getRollingWindowSize(values.length);
        const trendHalfWindow = Math.floor(trendWindowSize / 2);

        const pointData = values.map((value, index) => {
            const x = values.length > 1 ? (index / (values.length - 1)) * 100 : 50;
            const normalizedY = (value - min) / span;
            const y = 100 - normalizedY * 100;
            const freqHz = binsHz[index] ?? fallbackStartHz + fallbackStepHz * index;
            const windowStart = Math.max(0, index - trendHalfWindow);
            const windowEnd = Math.min(values.length, index + trendHalfWindow + 1);
            const windowSlice = values.slice(windowStart, windowEnd);
            const averageTrendDb = windowSlice.reduce((sum, pointValue) => sum + pointValue, 0) / windowSlice.length;
            const sortedWindowSlice = [...windowSlice].sort((a, b) => a - b);
            const medianTrendDb =
                sortedWindowSlice.length % 2 === 0
                    ? (sortedWindowSlice[sortedWindowSlice.length / 2 - 1] + sortedWindowSlice[sortedWindowSlice.length / 2]) / 2
                    : sortedWindowSlice[Math.floor(sortedWindowSlice.length / 2)];
            const averageTrendY = 100 - ((averageTrendDb - min) / span) * 100;
            const medianTrendY = 100 - ((medianTrendDb - min) / span) * 100;
            return { x, y, powerDb: value, freqHz, averageTrendDb, medianTrendDb, averageTrendY, medianTrendY };
        });

        const points = pointData.map(({ x, y }) => `${x},${y}`).join(' ');
        const averageTrendPoints = pointData.map(({ x, averageTrendY }) => `${x},${averageTrendY}`).join(' ');
        const medianTrendPoints = pointData.map(({ x, medianTrendY }) => `${x},${medianTrendY}`).join(' ');

        const averageNormalized = (mean - min) / span;
        const averageY = 100 - averageNormalized * 100;

        const medianNormalized = (median - min) / span;
        const medianY = 100 - medianNormalized * 100;

        return { points, averageTrendPoints, medianTrendPoints, averageY, medianY, min, max, mean, median, pointData };
    }, [payload]);

    useEffect(() => {
        if (hoveredIndex === null) {
            return;
        }
        if (hoveredIndex > chartData.pointData.length - 1) {
            setHoveredIndex(null);
        }
    }, [chartData.pointData.length, hoveredIndex]);

    useEffect(() => {
        if (!payload?.data || isEditingSignalConfig) {
            return;
        }

        setCenterFreqHzInput(String(payload.data.center_freq_hz));
        setBandwidthHzInput(String(payload.data.bandwidth_hz));
        setGainInput(String(payload.data.gain));
        setNAveInput(String(payload.data.n_ave));
    }, [payload, isEditingSignalConfig]);

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
    const startFreqMhz = formatMhz(data.center_freq_hz - data.bandwidth_hz / 2);
    const centerFreqMhz = formatMhz(data.center_freq_hz);
    const endFreqMhz = formatMhz(data.center_freq_hz + data.bandwidth_hz / 2);
    const maxPowerDb = chartData.max.toFixed(2);
    const meanPowerDb = chartData.mean.toFixed(2);
    const medianPowerDb = chartData.median.toFixed(2);
    const minPowerDb = chartData.min.toFixed(2);
    const hoveredPoint = hoveredIndex !== null ? chartData.pointData[hoveredIndex] : null;

    const selectedSeriesY =
        selectedSeries === 'average'
            ? hoveredPoint?.averageTrendY ?? chartData.averageY
            : selectedSeries === 'median'
              ? hoveredPoint?.medianTrendY ?? chartData.medianY
              : hoveredPoint?.y ?? chartData.averageY;
    const tooltipLeft = hoveredPoint ? `${(hoveredPoint.x / CHART_VIEWBOX_SIZE) * 100}%` : '0%';
    const tooltipTop = `${(selectedSeriesY / CHART_VIEWBOX_SIZE) * CHART_HEIGHT_PX}px`;

    const handleChartPointer = (event: MouseEvent<HTMLDivElement>) => {
        if (chartData.pointData.length === 0) {
            return;
        }

        const { left, width, top, height } = event.currentTarget.getBoundingClientRect();
        if (width <= 0 || height <= 0) {
            return;
        }

        const relativeX = (event.clientX - left) / width;
        const clampedX = Math.min(1, Math.max(0, relativeX));
        const nextIndex = Math.round(clampedX * (chartData.pointData.length - 1));
        setHoveredIndex(nextIndex);

        const hoveredY = ((event.clientY - top) / height) * 100;
        const spectrumY = chartData.pointData[nextIndex]?.y ?? chartData.averageY;

        const nearestSeries = (
            [
                { key: 'spectrum' as const, distance: Math.abs(hoveredY - spectrumY) },
                { key: 'average' as const, distance: Math.abs(hoveredY - (chartData.pointData[nextIndex]?.averageTrendY ?? chartData.averageY)) },
                { key: 'median' as const, distance: Math.abs(hoveredY - (chartData.pointData[nextIndex]?.medianTrendY ?? chartData.medianY)) },
            ]
        ).sort((a, b) => a.distance - b.distance)[0];

        setSelectedSeries(nearestSeries.key);
    };

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

        setIsSavingMode(true);
        try {
            const response = await axios.post<RadioPayload>(`${RADIO_ENDPOINT}/config`, submittedConfig);
            setPayload(response.data);
            setIsEditingSignalConfig(false);
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
                    onChange={(e) => {
                        setCenterFreqHzInput(e.target.value);
                        setIsEditingSignalConfig(true);
                    }}
                />
                <TextField
                    select
                    size='small'
                    label='Bandwidth (Hz)'
                    value={bandwidthHzInput}
                    disabled={isSavingMode}
                    onChange={(e) => {
                        setBandwidthHzInput(e.target.value);
                        setIsEditingSignalConfig(true);
                    }}
                >
                    <MenuItem value='1024000'>1024000</MenuItem>
                    <MenuItem value='2400000'>2400000</MenuItem>
                </TextField>
                <TextField
                    size='small'
                    label='Gain (auto or dB)'
                    value={gainInput}
                    disabled={isSavingMode}
                    onChange={(e) => {
                        setGainInput(e.target.value);
                        setIsEditingSignalConfig(true);
                    }}
                />
                <TextField
                    size='small'
                    label='N_Ave'
                    value={nAveInput}
                    disabled={isSavingMode}
                    onChange={(e) => {
                        setNAveInput(e.target.value);
                        setIsEditingSignalConfig(true);
                    }}
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

            <Box className='radio-chart-wrapper'>
                <Box className='radio-chart-row'>
                    <Box className='radio-chart__y-labels'>
                        <span>{maxPowerDb} dB</span>
                        <span>{meanPowerDb} dB (avg)</span>
                        <span>{medianPowerDb} dB (med)</span>
                        <span>{minPowerDb} dB</span>
                    </Box>
                    <Box
                        className='radio-chart-container'
                        onMouseMove={handleChartPointer}
                        onMouseLeave={() => setHoveredIndex(null)}
                    >
                        <svg viewBox='0 0 100 100' preserveAspectRatio='none' className='radio-chart'>
                            <polyline className='radio-chart__line' points={chartData.points} />
                            <polyline className='radio-chart__avg-line' points={chartData.averageTrendPoints} />
                            <polyline className='radio-chart__median-line' points={chartData.medianTrendPoints} />
                            {hoveredPoint && (
                                <>
                                    <line className='radio-chart__crosshair' x1={hoveredPoint.x} y1='0' x2={hoveredPoint.x} y2='100' />
                                    <circle
                                        className={`radio-chart__focus-point__glow ${selectedSeries === 'spectrum' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.y}
                                        r='2.8'
                                    />
                                    <circle
                                        className={`radio-chart__focus-point ${selectedSeries === 'spectrum' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.y}
                                        r='1.15'
                                    />
                                    <circle
                                        className={`radio-chart__focus-point__glow radio-chart__focus-point__glow--avg ${selectedSeries === 'average' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.averageTrendY}
                                        r='2.4'
                                    />
                                    <circle
                                        className={`radio-chart__focus-point radio-chart__focus-point--avg ${selectedSeries === 'average' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.averageTrendY}
                                        r='1.05'
                                    />
                                    <circle
                                        className={`radio-chart__focus-point__glow radio-chart__focus-point__glow--median ${selectedSeries === 'median' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.medianTrendY}
                                        r='2.4'
                                    />
                                    <circle
                                        className={`radio-chart__focus-point radio-chart__focus-point--median ${selectedSeries === 'median' ? 'is-selected' : ''}`}
                                        cx={hoveredPoint.x}
                                        cy={hoveredPoint.medianTrendY}
                                        r='1.05'
                                    />
                                </>
                            )}
                        </svg>
                        {hoveredPoint && (
                            <Box className='radio-chart__tooltip' sx={{ left: tooltipLeft, top: tooltipTop }}>
                                <Typography variant='caption' component='div'>
                                    {formatMhz(hoveredPoint.freqHz)} MHz
                                </Typography>
                                <Typography variant='caption' component='div'>
                                    Spectrum: {hoveredPoint.powerDb.toFixed(2)} dB
                                </Typography>
                                <Typography variant='caption' component='div'>
                                    Average trend: {hoveredPoint.averageTrendDb.toFixed(2)} dB
                                </Typography>
                                <Typography variant='caption' component='div'>
                                    Median trend: {hoveredPoint.medianTrendDb.toFixed(2)} dB
                                </Typography>
                                <Typography variant='caption' component='div'>
                                    Selected: {selectedSeries}
                                </Typography>
                            </Box>
                        )}
                    </Box>
                </Box>
                <Box className='radio-chart__x-labels'>
                    <span>{startFreqMhz} MHz</span>
                    <span>{centerFreqMhz} MHz</span>
                    <span>{endFreqMhz} MHz</span>
                </Box>
            </Box>

            <Typography variant='caption' display='block'>
                Last update: {new Date(data.timestamp * 1000).toLocaleTimeString()}
            </Typography>
        </Box>
    );
};
