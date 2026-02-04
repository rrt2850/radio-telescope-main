type CoordEntryProps = {
    mode: 'radec' | 'altaz';
    onChange: (coords: { ra: number; dec: number } | { az: number; alt: number }) => void;
    coords: { ra: number; dec: number } | { az: number; alt: number };
};

