import { Box, Typography } from '@mui/material';

type HydrogenSkyMapProps = {
    rows: number;
    cols: number;
    pixels: string[];
    isScanMode: boolean;
};

export const HydrogenSkyMap = ({ rows, cols, pixels, isScanMode }: HydrogenSkyMapProps) => {
    return (
        <Box className='hydrogen-map'>
            <Typography variant='subtitle2'>Neutral hydrogen map</Typography>
            <Typography variant='caption' color='text.secondary'>
                {isScanMode ? 'Scan mode: completed pixels are retained.' : 'Average mode: full map reflects current signal.'}
            </Typography>
            <Box
                className='hydrogen-map__grid'
                sx={{
                    gridTemplateColumns: `repeat(${cols}, 1fr)`,
                    gridTemplateRows: `repeat(${rows}, 1fr)`,
                }}
            >
                {pixels.map((pixel, index) => (
                    <Box key={index} className='hydrogen-map__pixel' sx={{ backgroundColor: pixel }} />
                ))}
            </Box>
        </Box>
    );
};
