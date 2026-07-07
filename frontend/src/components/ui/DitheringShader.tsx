import React, { useEffect, useRef, useState } from 'react';

interface DitheringShaderProps {
  shape?: 'wave' | 'noise';
  type?: '8x8';
  colorBack?: string;
  colorFront?: string;
  pxSize?: number;
  speed?: number;
  dithered?: boolean;
}

// Helper to convert hex strings (e.g. #071A1F) into normalized RGB float arrays [r, g, b]
const hexToRgb = (hex: string): [number, number, number] => {
  const cleanHex = hex.replace('#', '');
  if (cleanHex.length === 3) {
    const r = parseInt(cleanHex[0] + cleanHex[0], 16) / 255;
    const g = parseInt(cleanHex[1] + cleanHex[1], 16) / 255;
    const b = parseInt(cleanHex[2] + cleanHex[2], 16) / 255;
    return [r, g, b];
  }
  const r = parseInt(cleanHex.substring(0, 2), 16) / 255;
  const g = parseInt(cleanHex.substring(2, 4), 16) / 255;
  const b = parseInt(cleanHex.substring(4, 6), 16) / 255;
  return [r, g, b];
};

const VERTEX_SHADER_SOURCE = `#version 300 es
in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER_SOURCE = `#version 300 es
precision highp float;

uniform vec2 u_resolution;
uniform float u_time;
uniform vec3 u_colorBack;
uniform vec3 u_colorFront;
uniform float u_pxSize;
uniform float u_dithered;

out vec4 outColor;

// Bayer 8x8 matrix lookup
float bayer8(vec2 p) {
    int x = int(mod(p.x, 8.0));
    int y = int(mod(p.y, 8.0));
    int i = x + y * 8;
    
    float m[64] = float[](
        0.0, 48.0, 12.0, 60.0,  3.0, 51.0, 15.0, 63.0,
        32.0, 16.0, 44.0, 28.0, 35.0, 19.0, 47.0, 31.0,
        8.0, 56.0,  4.0, 52.0, 11.0, 59.0,  7.0, 55.0,
        40.0, 24.0, 36.0, 20.0, 43.0, 27.0, 39.0, 23.0,
        2.0, 50.0, 14.0, 62.0,  1.0, 49.0, 13.0, 61.0,
        34.0, 18.0, 46.0, 30.0, 33.0, 17.0, 45.0, 29.0,
        10.0, 58.0,  6.0, 54.0,  9.0, 57.0,  5.0, 53.0,
        42.0, 26.0, 38.0, 22.0, 41.0, 25.0, 37.0, 21.0
    );
    return m[i] / 64.0;
}

// Organic wave generator
float waveShape(vec2 uv, float time) {
    // Warp space to create a more liquid feel
    float warp = sin(uv.x * 2.5 + time * 0.4) * 0.12 + cos(uv.y * 1.8 + time * 0.25) * 0.08;
    
    // Wave layers
    float w1 = sin((uv.x + warp) * 3.1415 + time) * 0.15;
    float w2 = cos((uv.x - warp) * 1.5707 - time * 0.6) * 0.1;
    float w3 = sin(uv.x * 5.0 + time * 1.2) * 0.04;
    
    float baseHeight = 0.5 - (uv.x - 0.5) * 0.1;
    float waveHeight = baseHeight + w1 + w2 + w3;
    
    float dist = uv.y - waveHeight;
    return smoothstep(0.2, -0.2, dist);
}

void main() {
    vec2 pixelCoord = gl_FragCoord.xy / u_pxSize;
    vec2 pixelatedUV = floor(pixelCoord) * u_pxSize / u_resolution;
    vec2 uv = gl_FragCoord.xy / u_resolution;
    
    // Smooth wave shape calculation
    float waveVal = waveShape(u_dithered > 0.5 ? pixelatedUV : uv, u_time);
    
    vec3 col;
    if (u_dithered > 0.5) {
        // Get dither matrix threshold
        float threshold = bayer8(pixelCoord);
        // Select color based on threshold comparison
        col = (waveVal > threshold) ? u_colorFront : u_colorBack;
    } else {
        // Smooth mix for subtle wave background
        col = mix(u_colorBack, u_colorFront, waveVal * 0.22);
    }
    
    outColor = vec4(col, 1.0);
}
`;

export const DitheringShader: React.FC<DitheringShaderProps> = ({
  shape = 'wave',
  type = '8x8',
  colorBack = '#071A1F',
  colorFront = '#4FD1C5',
  pxSize = 2,
  speed = 0.25,
  dithered = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [webglSupported, setWebglSupported] = useState(true);
  const isVisibleRef = useRef(true);

  // Keep references updated to avoid re-initializing shaders when colors/props change
  const propsRef = useRef({ colorBack, colorFront, pxSize, speed, dithered });
  useEffect(() => {
    propsRef.current = { colorBack, colorFront, pxSize, speed, dithered };
  }, [colorBack, colorFront, pxSize, speed, dithered]);

  // Track visibility with IntersectionObserver to pause rendering when offscreen
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisibleRef.current = entry.isIntersecting;
      },
      { threshold: 0.01 }
    );

    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl2');
    if (!gl) {
      console.warn('WebGL2 is not supported in this browser. Falling back to static gradient.');
      setWebglSupported(false);
      return;
    }

    // Helper: compile shader
    const compileShader = (source: string, type: number): WebGLShader | null => {
      const shader = gl.createShader(type);
      if (!shader) return null;
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compilation error:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
      }
      return shader;
    };

    const vs = compileShader(VERTEX_SHADER_SOURCE, gl.VERTEX_SHADER);
    const fs = compileShader(FRAGMENT_SHADER_SOURCE, gl.FRAGMENT_SHADER);
    if (!vs || !fs) {
      setWebglSupported(false);
      return;
    }

    const program = gl.createProgram();
    if (!program) {
      setWebglSupported(false);
      return;
    }

    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(program));
      setWebglSupported(false);
      return;
    }

    gl.useProgram(program);

    // Setup full-screen quad vertices
    const vertices = new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
      -1,  1,
       1, -1,
       1,  1,
    ]);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const positionLoc = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(positionLoc);
    gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);

    // Get uniform locations
    const uResolution = gl.getUniformLocation(program, 'u_resolution');
    const uTime = gl.getUniformLocation(program, 'u_time');
    const uColorBack = gl.getUniformLocation(program, 'u_colorBack');
    const uColorFront = gl.getUniformLocation(program, 'u_colorFront');
    const uPxSize = gl.getUniformLocation(program, 'u_pxSize');
    const uDithered = gl.getUniformLocation(program, 'u_dithered');

    let animationFrameId: number;
    let accumulatedTime = 0;
    let lastTimestamp = performance.now();

    const render = (timestamp: number) => {
      const delta = (timestamp - lastTimestamp) / 1000;
      lastTimestamp = timestamp;

      // Update elapsed time ONLY if visible
      if (isVisibleRef.current) {
        accumulatedTime += delta * propsRef.current.speed;

        // Resize viewport dynamically to match bounds
        const width = canvas.clientWidth;
        const height = canvas.clientHeight;
        if (canvas.width !== width || canvas.height !== height) {
          canvas.width = width;
          canvas.height = height;
          gl.viewport(0, 0, width, height);
        }

        gl.clearColor(0, 0, 0, 1);
        gl.clear(gl.COLOR_BUFFER_BIT);

        // Upload uniforms
        gl.uniform2f(uResolution, canvas.width, canvas.height);
        gl.uniform1f(uTime, accumulatedTime);
        gl.uniform1f(uPxSize, propsRef.current.pxSize);
        gl.uniform1f(uDithered, propsRef.current.dithered ? 1.0 : 0.0);

        const rgbBack = hexToRgb(propsRef.current.colorBack);
        const rgbFront = hexToRgb(propsRef.current.colorFront);
        gl.uniform3f(uColorBack, rgbBack[0], rgbBack[1], rgbBack[2]);
        gl.uniform3f(uColorFront, rgbFront[0], rgbFront[1], rgbFront[2]);

        // Draw quad
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    // Cleanup resources
    return () => {
      cancelAnimationFrame(animationFrameId);
      gl.useProgram(null);
      gl.deleteProgram(program);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      gl.deleteBuffer(buffer);
    };
  }, []);

  // WebGL fallback container
  if (!webglSupported) {
    return (
      <div
        className="w-full h-full"
        style={{
          background: `linear-gradient(135deg, ${colorBack} 0%, ${colorFront} 100%)`,
        }}
      />
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full block pointer-events-none"
      style={{ display: 'block' }}
    />
  );
};

export default DitheringShader;
