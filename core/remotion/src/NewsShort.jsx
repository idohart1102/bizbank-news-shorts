import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT} from './fonts';

// Thứ tự lớp (decisions.md): ảnh nền → cutout → thẻ chữ/số → overlay.png (template trên cùng) ; câu hook dưới khung.
// Mọi lớp hình nằm trong khung 4:3 của template (layout.media) và bị cắt theo khung: phóng, lia, trượt
// đều không ra ngoài khung. Không có phụ đề.
const FADE = 6;

export const NewsShort = (props) => {
  const {fps} = useVideoConfig();
  const at = (seconds) => Math.round(seconds * fps);
  const brand = {navy: '#081840', lime: '#B8D03E', blue: '#4AA0EA', mint: '#B2E0CA', ...props.style};
  const box = props.layout.media;
  const local = (r) => ({...r, x: r.x - box.x, y: r.y - box.y});  // toạ độ trong khung
  const span = (item) => Math.max(1, at(item.end) - at(item.start));
  return (
    <AbsoluteFill style={{backgroundColor: brand.navy, fontFamily: FONT}}>
      <div style={{position: 'absolute', left: box.x, top: box.y, width: box.w, height: box.h, overflow: 'hidden'}}>
        {props.scenes.map((scene, i) => (
          // Cảnh kéo dài thêm FADE khung nằm dưới cảnh sau trong lúc cảnh sau hiện dần: không chớp nền.
          <Sequence key={`m${i}`} from={at(scene.start)}
            durationInFrames={Math.max(1, at(scene.end) - at(scene.start) + (i < props.scenes.length - 1 ? FADE : 0))}>
            <MediaScene scene={scene} fade={i > 0} />
          </Sequence>
        ))}
        {props.cutouts.map((item, i) => (
          <Sequence key={`c${i}`} from={at(item.start)} durationInFrames={span(item)}>
            <Cutout item={item} rect={local(props.layout.cutout)} />
          </Sequence>
        ))}
        {props.cards.map((card, i) => (
          <Sequence key={`k${i}`} from={at(card.start)} durationInFrames={span(card)}>
            <Card card={card} rect={local(props.layout.cards)} brand={brand} />
          </Sequence>
        ))}
      </div>
      {props.overlay ? <Img src={staticFile(props.overlay)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}} /> : null}
      {props.hook && props.layout.hook ? <Hook text={props.hook} rect={props.layout.hook} /> : null}
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

// Chuyển động trong giới hạn z (zoom_max tính từ độ phân giải ảnh gốc). Lia tối đa (z-1)/(2z) để mép ảnh
// không bao giờ lộ trong khung.
const MOTIONS = {
  'zoom-in': (p, z) => ({s: 1 + (z - 1) * p, x: 0, y: 0}),
  'zoom-out': (p, z) => ({s: z - (z - 1) * p, x: 0, y: 0}),
  'pan-left': (p, z, a) => ({s: z, x: a - 2 * a * p, y: 0}),
  'pan-right': (p, z, a) => ({s: z, x: -a + 2 * a * p, y: 0}),
  'ken-burns': (p, z, a) => {
    const s = 1 + (z - 1) * p;
    const b = ((s - 1) / (2 * s)) * 100 * 0.7;
    return {s, x: -b, y: -b * 0.6};
  },
  'static': () => ({s: 1, x: 0, y: 0}),
  'split': (p, z) => ({s: 1 + (z - 1) * p, x: 0, y: 0}),
};

const MediaScene = ({scene, fade}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const total = Math.max(1, Math.round((scene.end - scene.start) * fps));
  const p = interpolate(frame, [0, total], [0, 1], {extrapolateRight: 'clamp'});
  const z = Math.max(1, scene.zoom_max || 1.08);
  const a = ((z - 1) / (2 * z)) * 100 * 0.9;
  const m = (MOTIONS[scene.motion] || MOTIONS['ken-burns'])(p, z, a);
  const fadeIn = fade ? interpolate(frame, [0, FADE], [0, 1], {extrapolateRight: 'clamp'}) : 1;
  const src = staticFile(scene.src);
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      {scene.fit === 'contain' ? (
        // Ảnh văn bản/biểu đồ: hiện đủ, phía sau là chính ảnh đó làm mờ để không có viền trống
        <Img src={src} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
          filter: 'blur(30px) brightness(0.5)', transform: 'scale(1.2)'}} />
      ) : null}
      <Img src={src} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: scene.fit || 'cover',
        transform: `scale(${m.s}) translate(${m.x}%, ${m.y}%)`}} />
    </AbsoluteFill>
  );
};

// Cutout: trượt vào từ cạnh, nảy nhẹ, chân đặt ở đáy khung (dải mờ của template phủ lên chân, nhìn như đứng sau khung).
const Cutout = ({item, rect}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 13, stiffness: 120}});
  const leave = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const height = Math.min(rect.h * 0.86, 660);
  const width = Math.min(height * item.ratio, rect.w * 0.5);
  const right = item.side === 'right';
  const x = right ? rect.x + rect.w - width - 24 : rect.x + 24;
  const slide = (1 - enter) * (right ? 1 : -1) * (width + 40);
  const float = Math.sin(frame / 18) * 4;
  return (
    <Img src={staticFile(item.src)} style={{position: 'absolute', left: x + slide, top: rect.y + rect.h - height + float + 6,
      width, height, objectFit: 'contain', objectPosition: 'bottom', opacity: leave,
      filter: 'drop-shadow(0 0 2px #fff) drop-shadow(0 0 2px #fff) drop-shadow(0 14px 20px rgba(0,0,0,0.5))'}} />
  );
};

// Thẻ chữ/số theo nhận diện template: nền navy, ba vạch lá mạ/xanh/bạc hà, số trắng, nhãn bạc hà.
const Card = ({card, rect, brand}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 12, stiffness: 170}});
  const leave = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const beside = card.align !== 'center';
  const maxWidth = rect.w * (beside ? 0.58 : 0.74);
  const valueSize = Math.min(beside ? 76 : 88, Math.floor((maxWidth - 72) / Math.max(4, card.value.length * 0.58)));
  const anchor = card.align === 'right' ? {right: 0} : {left: 0};
  return (
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, opacity: leave}}>
      <div style={{position: 'absolute', bottom: 0, ...anchor, maxWidth, transformOrigin: card.align === 'right' ? 'right bottom' : 'left bottom',
        transform: `translateY(${(1 - pop) * 36}px) scale(${0.86 + 0.14 * pop})`,
        background: 'rgba(8,24,64,0.94)', borderRadius: 20, padding: '18px 32px 20px',
        boxShadow: '0 12px 30px rgba(0,0,0,0.45)', border: '1px solid rgba(178,224,202,0.25)'}}>
        <div style={{display: 'flex', gap: 8, marginBottom: 10}}>
          <span style={{width: 54, height: 7, borderRadius: 4, background: brand.lime}} />
          <span style={{width: 32, height: 7, borderRadius: 4, background: brand.blue}} />
          <span style={{width: 16, height: 7, borderRadius: 4, background: brand.mint}} />
        </div>
        <div style={{color: '#fff', fontWeight: 800, fontSize: valueSize, lineHeight: 1.04, letterSpacing: -0.5,
          whiteSpace: 'nowrap'}}>{card.value}</div>
        <div style={{color: brand.mint, fontWeight: 600, fontSize: beside ? 28 : 32, lineHeight: 1.2, marginTop: 6}}>{card.label}</div>
      </div>
    </div>
  );
};

// Câu hook < 100 ký tự, đứng yên suốt video dưới khung ảnh.
const Hook = ({text, rect}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 16}});
  const size = text.length > 70 ? 54 : text.length > 45 ? 60 : 68;
  return (
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, opacity: enter,
      transform: `translateY(${(1 - enter) * 20}px)`}}>
      <div style={{color: '#fff', fontWeight: 800, fontSize: size, lineHeight: 1.22, textWrap: 'balance'}}>{text}</div>
    </div>
  );
};
