import {Composition} from 'remotion';
import '@fontsource/be-vietnam-pro/600.css';
import '@fontsource/be-vietnam-pro/800.css';
import {NewsShort} from './NewsShort';
import {TempOverlay} from './TempOverlay';

// Props do core/news/render.py dựng từ edit_plan.json; xem NewsShort.jsx để biết cấu trúc.
const emptyProps = {fps: 30, width: 1080, height: 1920, duration: 3, layout: null, overlay: null, voice: null,
  scenes: [], cards: [], cutouts: [], sfx: [], music: null, style: {}};

export const Root = () => (
  <>
    <Composition id="NewsShort" component={NewsShort} defaultProps={emptyProps} fps={30} width={1080} height={1920}
      durationInFrames={90}
      calculateMetadata={({props}) => ({
        fps: props.fps, width: props.width, height: props.height,
        durationInFrames: Math.max(1, Math.ceil(props.duration * props.fps)),
      })} />
    <Composition id="TempOverlay" component={TempOverlay} fps={30} width={1080} height={1920} durationInFrames={1}
      defaultProps={{layout: null, title: 'BẢN TIN KINH DOANH'}} />
  </>
);
