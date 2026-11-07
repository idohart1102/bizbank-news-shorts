import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT} from './fonts';

// Thứ tự lớp cố định theo decisions.md: media → chữ nhấn → phụ đề → overlay.png (trên cùng).
export const NewsShort = (props) => {
  const {fps} = useVideoConfig();
  const at = (seconds) => Math.round(seconds * fps);
  const style = {accent: '#FFD400', text: '#FFFFFF', shadow: 'rgba(0,0,0,0.85)', ...props.style};
  return (
    <AbsoluteFill style={{backgroundColor: '#0b1622', fontFamily: FONT}}>
      {props.scenes.map((scene, i) => (
        // Cảnh kéo dài thêm FADE khung, nằm dưới cảnh sau trong lúc cảnh sau hiện dần: không lộ nền (chớp đen).
        <Sequence key={`m${i}`} from={at(scene.start)}
          durationInFrames={Math.max(1, at(scene.end) - at(scene.start) + (i < props.scenes.length - 1 ? FADE : 0))}>
          <MediaScene scene={scene} rect={props.layout.media} fade={i > 0} />
        </Sequence>
      ))}
      {props.scenes.filter((s) => s.headline).map((scene, i) => (
        <Sequence key={`h${i}`} from={at(scene.start)} durationInFrames={Math.max(1, at(scene.end) - at(scene.start))}>
          <Headline text={scene.headline} rect={props.layout.headline} style={style} />
        </Sequence>
      ))}
      {props.emphasis.map((item, i) => (
        <Sequence key={`e${i}`} from={at(item.start)} durationInFrames={Math.max(1, at(item.end) - at(item.start))}>
          <Emphasis text={item.text} rect={props.layout.emphasis || props.layout.media} style={style} />
        </Sequence>
      ))}
      <Subtitles captions={props.captions} rect={props.layout.subtitle} style={style} />
      {props.overlay ? <Img src={staticFile(props.overlay)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} /> : null}
      {props.voice ? <Audio src={staticFile(props.voice)} /> : null}
      {props.sfx.map((item, i) => (
        <Sequence key={`s${i}`} from={at(item.start)}>
          <Audio src={staticFile(item.src)} volume={item.volume} />
        </Sequence>
      ))}
      {props.music ? <Audio src={staticFile(props.music.src)} volume={props.music.volume} loop /> : null}
    </AbsoluteFill>
  );
};

const FADE = 6;

const MOTIONS = {
  'zoom-in': (p) => ({scale: 1 + 0.15 * p, x: 0, y: 0}),
  'zoom-out': (p) => ({scale: 1.15 - 0.15 * p, x: 0, y: 0}),
  'pan-left': (p) => ({scale: 1.15, x: 5 - 10 * p, y: 0}),
  'pan-right': (p) => ({scale: 1.15, x: -5 + 10 * p, y: 0}),
  'ken-burns': (p) => ({scale: 1.06 + 0.12 * p, x: -2 * p, y: -2 * p}),
  'static': () => ({scale: 1.02, x: 0, y: 0}),
  'split': (p) => ({scale: 1.05 + 0.05 * p, x: 0, y: 0}),
};

const MediaScene = ({scene, rect, fade}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const total = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const p = interpolate(frame, [0, total], [0, 1], {extrapolateRight: 'clamp'});
  const m = (MOTIONS[scene.motion] || MOTIONS['ken-burns'])(p);
  const fadeIn = fade ? interpolate(frame, [0, FADE], [0, 1], {extrapolateRight: 'clamp'}) : 1;
  const src = staticFile(scene.src);
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      {/* Nền: chính ảnh đó phóng to, làm mờ, để ảnh ngang không để lại viền đen */}
      <Img src={src} style={{position: 'absolute', width, height, objectFit: 'cover', filter: 'blur(40px) brightness(0.55)', transform: 'scale(1.2)'}} />
      <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, overflow: 'hidden'}}>
        <Img src={src} style={{width: '100%', height: '100%', objectFit: scene.fit || 'cover',
          transform: `scale(${m.scale}) translate(${m.x}%, ${m.y}%)`}} />
      </div>
    </AbsoluteFill>
  );
};

const Headline = ({text, rect, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 14}});
  // Ưu tiên một dòng: co chữ theo độ dài (≥ 44px), dài quá mới xuống dòng; không để chữ cuối đứng lẻ.
  const fontSize = Math.max(44, Math.min(58, Math.floor((rect.w - 40) / Math.max(1, text.length * 0.56))));
  return (
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, display: 'flex',
      alignItems: 'center', justifyContent: 'center', transform: `scale(${0.9 + 0.1 * pop})`, opacity: pop}}>
      <div style={{color: style.text, fontWeight: 800, fontSize, lineHeight: 1.15, textAlign: 'center', textWrap: 'balance',
        textShadow: `0 4px 12px ${style.shadow}`}}>{text}</div>
    </div>
  );
};

const Emphasis = ({text, rect, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 11, stiffness: 160}});
  // Co chữ theo độ dài để khung không chạm mép (ước lượng bề rộng ký tự ~0,6em, chừa lề 120px).
  const fontSize = Math.min(76, Math.floor((rect.w - 120) / Math.max(1, text.length * 0.6)));
  return (
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, display: 'flex',
      alignItems: 'center', justifyContent: 'center'}}>
      <div style={{background: style.accent, color: '#111', fontWeight: 800, fontSize, padding: '14px 34px',
        borderRadius: 18, transform: `scale(${pop}) rotate(${(1 - pop) * -4}deg)`, boxShadow: '0 10px 30px rgba(0,0,0,0.45)',
        textAlign: 'center', maxWidth: rect.w}}>{text}</div>
    </div>
  );
};

const Subtitles = ({captions, rect, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const current = captions.find((c) => t >= c.start && t < c.end);
  if (!current) return null;
  return (
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, display: 'flex',
      alignItems: 'center', justifyContent: 'center', textAlign: 'center'}}>
      <div style={{fontWeight: 800, fontSize: 62, lineHeight: 1.22, color: style.text,
        textShadow: `0 0 10px ${style.shadow}, 0 4px 8px ${style.shadow}`, WebkitTextStroke: `2px ${style.shadow}`,
        paintOrder: 'stroke fill'}}>
        {current.words.map((w, i) => (
          <span key={i} style={{color: t >= w.start ? style.accent : style.text}}>{w.text}{i < current.words.length - 1 ? ' ' : ''}</span>
        ))}
      </div>
    </div>
  );
};
