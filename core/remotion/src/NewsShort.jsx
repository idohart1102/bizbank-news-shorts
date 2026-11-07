import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT} from './fonts';

// Thứ tự lớp (decisions.md): media → cutout → thẻ chữ/số → overlay.png (template trên cùng).
// Không có phụ đề. Thẻ và cutout chỉ nằm trong vùng ảnh (nửa trên) vì khung template che phần dưới.
const FADE = 6;

export const NewsShort = (props) => {
  const {fps} = useVideoConfig();
  const at = (seconds) => Math.round(seconds * fps);
  const brand = {navy: '#0B2A6B', lime: '#C3D82E', cyan: '#22A6E8', mint: '#A8E0D0', ...props.style};
  const span = (item) => Math.max(1, at(item.end) - at(item.start));
  return (
    <AbsoluteFill style={{backgroundColor: brand.navy, fontFamily: FONT}}>
      {props.scenes.map((scene, i) => (
        // Cảnh kéo dài thêm FADE khung nằm dưới cảnh sau trong lúc cảnh sau hiện dần: không chớp nền.
        <Sequence key={`m${i}`} from={at(scene.start)}
          durationInFrames={Math.max(1, at(scene.end) - at(scene.start) + (i < props.scenes.length - 1 ? FADE : 0))}>
          <MediaScene scene={scene} rect={props.layout.media} fade={i > 0} />
        </Sequence>
      ))}
      {props.cutouts.map((item, i) => (
        <Sequence key={`c${i}`} from={at(item.start)} durationInFrames={span(item)}>
          <Cutout item={item} rect={props.layout.cutout} />
        </Sequence>
      ))}
      {props.cards.map((card, i) => (
        <Sequence key={`k${i}`} from={at(card.start)} durationInFrames={span(card)}>
          <Card card={card} rect={props.layout.cards} brand={brand} />
        </Sequence>
      ))}
      {props.overlay ? <Img src={staticFile(props.overlay)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} /> : null}
      {props.voice ? <Audio src={staticFile(props.voice)} /> : null}
      {props.sfx.map((item, i) => (
        <Sequence key={`s${i}`} from={at(item.start)}>
          <Audio src={staticFile(item.src)} volume={item.volume} />
        </Sequence>
      ))}
      {props.music ? <Music music={props.music} duration={props.duration} /> : null}
    </AbsoluteFill>
  );
};

// Nhạc nền nhỏ xuyên suốt video: lặp nếu ngắn hơn video, fade vào/ra.
const Music = ({music, duration}) => {
  const {fps} = useVideoConfig();
  const total = Math.round(duration * fps);
  const volume = (f) => music.volume * interpolate(f, [0, music.fade_in * fps, total - music.fade_out * fps, total],
    [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <Audio src={staticFile(music.src)} volume={volume} loop />;
};

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
  const {fps} = useVideoConfig();
  const total = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const p = interpolate(frame, [0, total], [0, 1], {extrapolateRight: 'clamp'});
  const m = (MOTIONS[scene.motion] || MOTIONS['ken-burns'])(p);
  const fadeIn = fade ? interpolate(frame, [0, FADE], [0, 1], {extrapolateRight: 'clamp'}) : 1;
  const src = staticFile(scene.src);
  const box = {position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, overflow: 'hidden'};
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      <div style={box}>
        {/* Nền: chính ảnh đó phóng to, làm mờ, để ảnh văn bản/ảnh ngang không để lại viền trống */}
        <Img src={src} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
          filter: 'blur(36px) brightness(0.55)', transform: 'scale(1.25)'}} />
        <Img src={src} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: scene.fit || 'cover',
          transform: `scale(${m.scale}) translate(${m.x}%, ${m.y}%)`}} />
      </div>
    </AbsoluteFill>
  );
};

// Cutout (người được nhắc tên, sự vật quan trọng): trượt vào từ cạnh, nảy nhẹ, chân đặt ở mép dưới vùng ảnh.
const Cutout = ({item, rect}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 13, stiffness: 120}});
  const leave = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const height = Math.min(rect.h * 0.92, 640);
  const width = Math.min(height * item.ratio, rect.w * 0.55);
  const right = item.side === 'right';
  const x = right ? rect.x + rect.w - width - 30 : rect.x + 30;
  const slide = (1 - enter) * (right ? 1 : -1) * (width + 60);
  const float = Math.sin(frame / 18) * 4;
  return (
    <Img src={staticFile(item.src)} style={{position: 'absolute', left: x + slide, top: rect.y + rect.h - height + float + 8,
      width, height, objectFit: 'contain', objectPosition: 'bottom', opacity: leave,
      filter: 'drop-shadow(0 0 2px #fff) drop-shadow(0 0 2px #fff) drop-shadow(0 16px 22px rgba(0,0,0,0.55))'}} />
  );
};

// Thẻ chữ/số: giá trị lớn + nhãn nhỏ, màu nhận diện, bật lên đúng lúc được đọc.
const Card = ({card, rect, brand}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 12, stiffness: 170}});
  const leave = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const narrow = card.align !== 'center';
  const width = narrow ? rect.w * 0.6 : Math.min(rect.w, 860);
  const left = card.align === 'left' ? rect.x : card.align === 'right' ? rect.x + rect.w - width : rect.x + (rect.w - width) / 2;
  const valueSize = Math.min(narrow ? 84 : 104, Math.floor((width - 70) / Math.max(1, card.value.length * 0.6)));
  return (
    <div style={{position: 'absolute', left, top: rect.y + rect.h - 230, width, opacity: leave,
      transform: `translateY(${(1 - pop) * 40}px) scale(${0.85 + 0.15 * pop})`, transformOrigin: 'center bottom'}}>
      <div style={{background: '#fff', borderRadius: 22, overflow: 'hidden', boxShadow: '0 14px 34px rgba(0,0,0,0.45)',
        borderLeft: `14px solid ${brand.lime}`}}>
        <div style={{padding: '14px 28px 4px', color: brand.navy, fontWeight: 800, fontSize: valueSize, lineHeight: 1.05,
          letterSpacing: -1}}>{card.value}</div>
        <div style={{padding: '0 28px 16px', color: '#3a4a6b', fontWeight: 600, fontSize: narrow ? 30 : 36, lineHeight: 1.2}}>
          {card.label}</div>
      </div>
    </div>
  );
};
