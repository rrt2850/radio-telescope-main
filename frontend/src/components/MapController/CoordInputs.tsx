import React, { useMemo } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { CoordRow } from './CoordRow';

type Star = {
    name: string;
    ra: number;
    dec: number;
    parallax_mas: number;
};

type CoordInputsProps = {
    coordMode: 'radec' | 'altaz';
    ra: string;
    dec: string;
    alt: string;
    az: string;
    onChange: (field: 'ra' | 'dec' | 'alt' | 'az', value: string) => void;
    stars: Star[];
    onSelectStar: (star: Star | null) => void;
};

export const CoordInputs = ({
    coordMode,
    ra,
    dec,
    alt,
    az,
    onChange,
    stars,
    onSelectStar,
}: CoordInputsProps) => {
    const selectedStar = useMemo(
        () => stars.find((star) => star.ra.toString() === ra && star.dec.toString() === dec) ?? null,
        [stars, ra, dec],
    );

    return coordMode === 'radec' ? (
        <>
            <Autocomplete
                options={stars}
                value={selectedStar}
                size='small'
                onChange={(_, value) => onSelectStar(value)}
                isOptionEqualToValue={(option, value) =>
                    option.name === value.name && option.ra === value.ra && option.dec === value.dec
                }
                getOptionLabel={(option) => option.name}
                filterOptions={(options, state) => {
                    const input = state.inputValue.trim().toLowerCase();
                    if (!input) {
                        return options.slice(0, 200);
                    }

                    return options
                        .filter((option) => option.name.toLowerCase().includes(input))
                        .slice(0, 200);
                }}
                renderOption={(props, option) => (
                    <li {...props} key={`${option.name}|${option.ra}|${option.dec}`}>
                        {`${option.name} (RA ${option.ra.toFixed(3)}, Dec ${option.dec.toFixed(3)})`}
                    </li>
                )}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        label='Search star catalog'
                        helperText='Type to filter stars from data.csv'
                    />
                )}
            />
            <CoordRow label='RA' value={ra} onChange={(v) => onChange('ra', v)} />
            <CoordRow label='Dec' value={dec} onChange={(v) => onChange('dec', v)} />
        </>
    ) : (
        <>
            <CoordRow label='Alt' value={alt} onChange={(v) => onChange('alt', v)} />
            <CoordRow label='Az' value={az} onChange={(v) => onChange('az', v)} />
        </>
    );
};
