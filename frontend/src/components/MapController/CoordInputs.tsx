import React, { useEffect, useState } from 'react';
import { Autocomplete, Box, Button, CircularProgress, TextField, Typography } from '@mui/material';
import { CoordRow } from './CoordRow';

type Star = {
    name: string;
    ra: number;
    dec: number;
    parallax_mas: number;
};

const BROWSE_PAGE_SIZE = 100;

type CoordInputsProps = {
    coordMode: 'radec' | 'altaz';
    ra: string;
    dec: string;
    alt: string;
    az: string;
    onChange: (field: 'ra' | 'dec' | 'alt' | 'az', value: string) => void;
    initialBrowseStars: Star[];
    onLoadBrowsePage: (page: number, pageSize: number) => Promise<Star[]>;
    onSearchStars: (query: string, limit?: number) => Promise<Star[]>;
    onSelectStar: (star: Star | null) => void;
};

export const CoordInputs = ({
    coordMode,
    ra,
    dec,
    alt,
    az,
    onChange,
    initialBrowseStars,
    onLoadBrowsePage,
    onSearchStars,
    onSelectStar,
}: CoordInputsProps) => {
    const [inputValue, setInputValue] = useState('');
    const [options, setOptions] = useState<Star[]>(initialBrowseStars);
    const [isLoading, setIsLoading] = useState(false);
    const [browsePage, setBrowsePage] = useState(0);
    const [hasMoreBrowse, setHasMoreBrowse] = useState(true);
    const [isSearchMode, setIsSearchMode] = useState(false);
    const [selectedStar, setSelectedStar] = useState<Star | null>(null);

    useEffect(() => {
        setOptions(initialBrowseStars);
        setBrowsePage(0);
        setHasMoreBrowse(initialBrowseStars.length >= BROWSE_PAGE_SIZE);
    }, [initialBrowseStars]);

    useEffect(() => {
        const query = inputValue.trim();
        const debounce = window.setTimeout(async () => {
            if (!query) {
                setIsSearchMode(false);
                setOptions(initialBrowseStars);
                setBrowsePage(0);
                setHasMoreBrowse(initialBrowseStars.length >= BROWSE_PAGE_SIZE);
                return;
            }

            try {
                setIsLoading(true);
                setIsSearchMode(true);
                const results = await onSearchStars(query, 50);
                setOptions(results);
                setHasMoreBrowse(false);
            } catch (error) {
                console.error('Error searching star catalog:', error);
                setOptions([]);
            } finally {
                setIsLoading(false);
            }
        }, 250);

        return () => {
            window.clearTimeout(debounce);
        };
    }, [inputValue, initialBrowseStars, onSearchStars]);

    const loadMoreBrowse = async () => {
        const nextPage = browsePage + 1;
        try {
            setIsLoading(true);
            const nextStars = await onLoadBrowsePage(nextPage, BROWSE_PAGE_SIZE);
            setOptions((prev) => [...prev, ...nextStars]);
            setBrowsePage(nextPage);
            if (nextStars.length < BROWSE_PAGE_SIZE) {
                setHasMoreBrowse(false);
            }
        } catch (error) {
            console.error('Error loading next star page:', error);
            setHasMoreBrowse(false);
        } finally {
            setIsLoading(false);
        }
    };


    return coordMode === 'radec' ? (
        <>
            <Autocomplete
                options={options}
                value={selectedStar}
                size='small'
                onChange={(_, value) => {
                    setSelectedStar(value);
                    onSelectStar(value);
                }}
                inputValue={inputValue}
                onInputChange={(_, value, reason) => {
                    if (reason === 'clear') {
                        setInputValue('');
                        setSelectedStar(null);
                        onSelectStar(null);
                        return;
                    }

                    if (reason === 'input') {
                        setInputValue(value);
                        if (selectedStar) {
                            setSelectedStar(null);
                        }
                        return;
                    }

                    if (reason === 'selectOption') {
                        setInputValue(value);
                    }
                }}
                isOptionEqualToValue={(option, value) =>
                    option.name === value.name && option.ra === value.ra && option.dec === value.dec
                }
                getOptionLabel={(option) => option.name}
                filterOptions={(x) => x}
                loading={isLoading}
                renderOption={(props, option) => (
                    <li {...props} key={`${option.name}|${option.ra}|${option.dec}`}>
                        {`${option.name} (RA ${option.ra.toFixed(3)}, Dec ${option.dec.toFixed(3)})`}
                    </li>
                )}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        label='Search star catalog'
                        helperText={isSearchMode ? 'Searching full server catalog' : 'Viewing stars in batches'}
                        slotProps={{
                            input: {
                                ...params.InputProps,
                                endAdornment: (
                                    <>
                                        {isLoading && <CircularProgress color='inherit' size={16} />}
                                        {params.InputProps.endAdornment}
                                    </>
                                ),
                            },
                        }}
                    />
                )}
            />
            {!isSearchMode && (
                <Box display='flex' justifyContent='space-between' alignItems='center' sx={{ mt: 0.5 }}>
                    <Typography variant='caption'>Loaded {options.length} stars</Typography>
                    <Button size='small' onClick={loadMoreBrowse} disabled={!hasMoreBrowse || isLoading}>
                        {hasMoreBrowse ? 'Load more' : 'End of catalog'}
                    </Button>
                </Box>
            )}
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
