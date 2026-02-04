import React from 'react';
import { CoordRow } from './CoordRow';

type CoordInputsProps = {
    coordMode: 'radec' | 'altaz';
    ra: string;
    dec: string;
    alt: string;
    az: string;
    onChange: (field: 'ra' | 'dec' | 'alt' | 'az', value: string) => void;
};

export const CoordInputs = ({
    coordMode,
    ra,
    dec,
    alt,
    az,
    onChange,
}: CoordInputsProps) =>
    coordMode === 'radec' ? (
        <>
            <CoordRow label="RA" value={ra} onChange={(v) => onChange('ra', v)} />
            <CoordRow label="Dec" value={dec} onChange={(v) => onChange('dec', v)} />
        </>
    ) : (
        <>
            <CoordRow label="Alt" value={alt} onChange={(v) => onChange('alt', v)} />
            <CoordRow label="Az" value={az} onChange={(v) => onChange('az', v)} />
        </>
    );
