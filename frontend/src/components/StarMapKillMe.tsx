import React, { useEffect, useRef } from "react";
import {
	WWTControlBuilder,
	WWTControl,
	ScriptInterface,
} from "@wwtelescope/engine";

export interface StarMapProps {
	ra: number; // degrees
	dec: number; // degrees
	fov: number; // degrees
	onChange?: (ra: string, dec: string, fov: string) => void;
}

export const StarMap2: React.FC<StarMapProps> = ({
	ra,
	dec,
	fov,
	onChange,
}) => {
	const containerRef = useRef<HTMLDivElement | null>(null);
	const scriptInterfaceRef = useRef<ScriptInterface | null>(null);
	const rafRef = useRef<number | null>(null);

	useEffect(() => {
		if (!containerRef.current) return;

		const div = containerRef.current;
		if (!div.id) {
			div.id = `wwt-canvas-${Math.random().toString(36).substring(2, 8)}`;
		}

		// Initialize WWT, auto-creates a <canvas> in the div
		const builder = new WWTControlBuilder(div.id);
		const scriptInterface = builder.create();
		scriptInterfaceRef.current = scriptInterface;

		// Load a background sky (Digitized Sky Survey = DSS)
		scriptInterface.loadImageCollection(
			"https://data1.wwtassets.org/packages/2023/07_jwst/weic2316a/index.wtml"
		);

		// Jump to initial RA/Dec/FOV after init
		setTimeout(() => {
			WWTControl.singleton.gotoRADecZoom(ra / 15, dec, fov * 6, true);
		}, 0);

		return () => {
			scriptInterfaceRef.current = null;
			if (rafRef.current) cancelAnimationFrame(rafRef.current);
		};
	}, []);

	// Respond to prop changes
	useEffect(() => {
		if (scriptInterfaceRef.current) {
			WWTControl.singleton.gotoRADecZoom(ra / 15, dec, fov * 6, true);
		}
	}, [ra, dec, fov]);

	// Track camera changes
	useEffect(() => {
		if (!scriptInterfaceRef.current || !onChange) return;

		let lastRa = NaN;
		let lastDec = NaN;
		let lastFov = NaN;

		const checkCamera = () => {
			const renderContext = WWTControl.singleton.renderContext;
			const cam = renderContext.viewCamera;

			const currentRa = cam.get_RA() * 15; // convert hours back to degrees
			const currentDec = cam.get_dec();
			const currentFov = renderContext.get_fovLocal() / 6; // back to degrees

			if (
				currentRa !== lastRa ||
				currentDec !== lastDec ||
				currentFov !== lastFov
			) {
				lastRa = currentRa;
				lastDec = currentDec;
				lastFov = currentFov;
				onChange(String(currentRa), String(currentDec), String(currentFov));
			}

			rafRef.current = requestAnimationFrame(checkCamera);
		};

		checkCamera();

		return () => {
			if (rafRef.current) cancelAnimationFrame(rafRef.current);
		};
	}, [onChange]);

	return (
		<div
			ref={containerRef}
			style={{ width: "100%", height: "500px", border: "1px solid #ccc" }}
		/>
	);
};
