import React, { useRef } from "react";

interface StarMapProps {
	ra: number;   // degrees
	dec: number;  // degrees
	fov: number;  // degrees
}

export const StarMap: React.FC<StarMapProps> = ({ ra, dec, fov }) => {
	const iframeRef = useRef<HTMLIFrameElement>(null);

	return (
		<iframe
			ref={iframeRef}
			src="https://web.wwtassets.org/embed/1/wwt/?cred=no&amp;cro=&amp;ch="
			width="1200"
			height="800"
			style={{ border: "none" }}
			title="WorldWide Telescope"
		/>
	);
};
