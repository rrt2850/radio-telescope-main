import { Grid, Typography, TextField, Box } from '@mui/material';

type CoordRowProps = {
    label: string;
    value: string;
    onChange: (v: string) => void;
}

export const CoordRow = ({ label, value, onChange }: CoordRowProps) => (
    <Box display="flex" alignItems="center" gap={1}>
        <Box width={48}>
            <Typography variant="body1">{label}:</Typography>
        </Box>
        <TextField
            type="number"
            size="small"
            value={value}
            onChange={(e) => onChange(e.target.value)}
        />
    </Box>
);

