import React from 'react';
import { ListSubheader, MenuItem, TextField } from '@mui/material';
import { CoordRow } from './CoordRow';

type Star = {
    name: string;
    ra: number;
    dec: number;
    parallax_mas: number;
};

type StarGroup = {
    group: string;
    stars: Star[];
};

type CoordInputsProps = {
    coordMode: 'radec' | 'altaz';
    ra: string;
    dec: string;
    alt: string;
    az: string;
    onChange: (field: 'ra' | 'dec' | 'alt' | 'az', value: string) => void;
    starGroups: StarGroup[];
    onSelectStar: (selectedKey: string) => void;
};

export const CoordInputs = ({
    coordMode,
    ra,
    dec,
    alt,
    az,
    onChange,
    starGroups,
    onSelectStar,
}: CoordInputsProps) =>
    coordMode === 'radec' ? (
        <>
            <TextField
                select
                label='Select a star'
                size='small'
                defaultValue=''
                onChange={(event) => onSelectStar(event.target.value)}
                helperText='Grouped by estimated distance from parallax'
            >
                <MenuItem value=''>Choose a star…</MenuItem>
                {starGroups.flatMap((group) => [
                    <ListSubheader key={`${group.group}-header`}>{group.group}</ListSubheader>,
                    ...group.stars.map((star) => (
                        <MenuItem
                            key={`${star.name}|${star.ra}|${star.dec}`}
                            value={`${star.name}|${star.ra}|${star.dec}`}
                        >
                            {`${star.name} (RA ${star.ra.toFixed(3)}, Dec ${star.dec.toFixed(3)})`}
                        </MenuItem>
                    )),
                ])}
            </TextField>
            <CoordRow label='RA' value={ra} onChange={(v) => onChange('ra', v)} />
            <CoordRow label='Dec' value={dec} onChange={(v) => onChange('dec', v)} />
        </>
    ) : (
        <>
            <CoordRow label='Alt' value={alt} onChange={(v) => onChange('alt', v)} />
            <CoordRow label='Az' value={az} onChange={(v) => onChange('az', v)} />
        </>
    );
