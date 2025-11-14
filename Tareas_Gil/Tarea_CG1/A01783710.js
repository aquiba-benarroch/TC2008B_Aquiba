/*
 * Tarea_CG1
 *
 * Aquiba Yudah Benarroch Bittan A01783710 
 * 2025-11-12
 */


'use strict';

import * as twgl from 'twgl-base.js';
import { M3 } from '../Tarea_CG1/A01783710_2d-lib.js';
import GUI from 'lil-gui';
import { diamond } from '../Tarea_CG1/shapes.js';

// Define the shader code, using GLSL 3.00

const vsGLSL = `#version 300 es
in vec2 a_position;

uniform vec2 u_resolution;
uniform mat3 u_transforms;

void main() {
    // Multiply the matrix by the vector, adding 1 to the vector to make
    // it the correct size. Then keep only the two first components.
    vec2 position = (u_transforms * vec3(a_position, 1)).xy;

    // Convert the position from pixels to 0.0 - 1.0
    vec2 zeroToOne = position / u_resolution;

    // Convert from 0->1 to 0->2
    vec2 zeroToTwo = zeroToOne * 2.0;

    // Convert from 0->2 to -1->1 (clip space)
    vec2 clipSpace = zeroToTwo - 1.0;

    // Invert Y axis
    //gl_Position = vec4(clipSpace[0], clipSpace[1] * -1.0, 0, 1);
    gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
}
`;

const fsGLSL = `#version 300 es
precision highp float;

uniform vec4 u_color;

out vec4 outColor;

void main() {
    outColor = u_color;
}
`;

// Structure to hold the data for each object
// This data will be modified by the UI and used by the renderer
class Object2D {
    constructor(
        id, t = [0, 0], rr = [0, 0, 0], s = [1, 1], color = [1, 1, 1, 1]
    ) {
        this.id = id //Identifier
        this.t = { //Translation
            x: t[0], 
            y: t[1]
        }
        this.rr = { //Rotation
            x: rr[0],
            y: rr[1],
            z: rr[2]
        }
        this.s = { //Scale
            x: s[0],
            y: s[1]
        }
        this.color = color //Color
    }
}

const objects = {
    pivot: new Object2D(
        'pivot',
        [400, 300],
        [0, 0, 0],
        [1, 1],
        [1, 0, 0, 1]
    ),
    face: new Object2D(
        'face',
        [700, 300],
        [0, 0, 0],
        [1, 1],
        [1, 1, 0, 1],
    ),
    leftEye: new Object2D(
        'leftEye',
        [0, 0],
        [0, 0, 0],
        [1, 1],
        [0, 0, 0, 1]
    ),
    rightEye: new Object2D(
        'rightEye',
        [0, 0],
        [0, 0, 0],
        [1, 1],
        [0, 0, 0, 1]
    ),
    mouth: new Object2D(
        'mouth',
        [0, 0],
        [0, 0, 0],
        [1, 1],
        [0, 0, 0, 1]
    )
}

//Initialize the WebGL environmnet
function main() {

    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2');
    twgl.resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    setupUI(gl);

    const programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    //Pivot: Importamos diamante de shapes 
    const pivotArrays = diamond(30);
    // Crear buffers y VAO para el pivote
    const pivotBufferInfo = twgl.createBufferInfoFromArrays(gl, pivotArrays);
    const pivotVAO = twgl.createVAOFromBufferInfo(gl, programInfo, pivotBufferInfo);

    //Cara
    const faceArrays = generateData(30, 0, 0, 100);
    //Crear buffers y VAO para la cara. Posicionada en el origen
    const faceBufferInfo = twgl.createBufferInfoFromArrays(gl, faceArrays);
    const faceVAO = twgl.createVAOFromBufferInfo(gl, programInfo, faceBufferInfo);

    //Ojo izquierdo. Posicionado en (-10, -50) para que quede relativo a la cara
    const leftEyeArrays = generateData(10, -10, -50, 15);
    //Crear buffers y VAO para el ojo izquierdo
    const leftEyeBufferInfo = twgl.createBufferInfoFromArrays(gl, leftEyeArrays);
    const leftEyeVAO = twgl.createVAOFromBufferInfo(gl, programInfo, leftEyeBufferInfo);

    //Ojo derecho. Posicionado en (10, -50) para que quede relativo a la cara
    const rightEyeArrays = generateData(20, 10, -50, 15);
    //Crear buffers y VAO para el ojo derecho
    const rightEyeBufferInfo = twgl.createBufferInfoFromArrays(gl, rightEyeArrays);
    const rightEyeVAO = twgl.createVAOFromBufferInfo(gl, programInfo, rightEyeBufferInfo);

    //Boca. Posicionada en (0, 40) para que quede relativa a la cara
    const mouthArrays = generateData(15, 0, 40, 25);
    //Crear buffers y VAO para la boca
    const mouthBufferInfo = twgl.createBufferInfoFromArrays(gl, mouthArrays);
    const mouthVAO = twgl.createVAOFromBufferInfo(gl, programInfo, mouthBufferInfo);

    //Llamar a la función de drawScene
    drawScene(gl, pivotVAO, faceVAO, leftEyeVAO, rightEyeVAO, mouthVAO, programInfo, pivotBufferInfo, faceBufferInfo, leftEyeBufferInfo, rightEyeBufferInfo, mouthBufferInfo);
}

// Function to do the actual display of the objects
function drawScene(gl, pivotVAO, faceVAO, leftEyeVAO, rightEyeVAO, mouthVAO, programInfo, pivotBufferInfo, faceBufferInfo, leftEyeBufferInfo, rightEyeBufferInfo, mouthBufferInfo) {
    gl.useProgram(programInfo.program);

    // Para el pivote
    let translate = [objects.pivot.t.x, objects.pivot.t.y];
    let angle_radians = objects.pivot.rr.z;
    let scale = [objects.pivot.s.x, objects.pivot.s.y];

    //Crear las matrices para las transformaciones
    const scaMat = M3.scale(scale);
    const rotMat = M3.rotation(angle_radians);
    const traMat = M3.translation(translate);

    //Hacer primero la escala, luego rotación y al final traslación
    let transforms = M3.identity();
    transforms = M3.multiply(scaMat, transforms);
    transforms = M3.multiply(rotMat, transforms);
    transforms = M3.multiply(traMat, transforms);

    //Guardar las transformaciones del pivote para usarlas en la cara
    const pivotTransforms = transforms;

    let uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms,
        u_color: objects.pivot.color,
    }
    
    //Dibujar el pivote
    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(pivotVAO);
    twgl.drawBufferInfo(gl, pivotBufferInfo);

    //Para la cara. Necesitamos rotarla alrededor del pivote
    //Primero aplicamos las transformaciones del pivote
    angle_radians = objects.face.rr.z;
    scale = [objects.face.s.x, objects.face.s.y];


    /*Para poder rotar alrededor del pivote lo que se hace es trasladar la cara al pivote, 
    rotar, y luego regresar. Esto debido a que si no lo hacemos asi la rotacion se haria 
    alrededor del origen de coordenadas
    */
    //Orden de transformaciones para rotar alrededor del pivote:
    transforms = M3.identity();
    //Debemos escalar primero
    transforms = M3.multiply(M3.scale(scale), transforms);
    //Trasladamos a la posición de la cara
    transforms = M3.multiply(M3.translation([objects.face.t.x, objects.face.t.y]), transforms);
    //Movemos el pivote al origen
    transforms = M3.multiply(M3.translation([-objects.pivot.t.x, -objects.pivot.t.y]), transforms);
    //Rotamos alrededor del origen
    transforms = M3.multiply(M3.rotation(angle_radians), transforms);
    //Movemos el pivote de vuelta a su posición
    transforms = M3.multiply(M3.translation([objects.pivot.t.x, objects.pivot.t.y]), transforms);
    //Guardamos esto para despues usarlo en los ojos y la boca
    const faceTransforms = transforms;

    uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms,
        u_color: objects.face.color,
    }

    //Dibujamos la cara
    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(faceVAO);
    twgl.drawBufferInfo(gl, faceBufferInfo);

    //Para el ojo izquierdo
    //Primero aplicamos transformaciones locales del ojo (posición relativa)
    translate = [-30, 30]; // Posición relativa a la cara
    angle_radians = objects.leftEye.rr.z;
    scale = [objects.leftEye.s.x, objects.leftEye.s.y];

    const scaMat3 = M3.scale(scale);
    const rotMat3 = M3.rotation(angle_radians);
    const traMat3 = M3.translation(translate);

    //HAcemos la escala, luego rotación y al final traslación
    transforms = M3.identity();
    transforms = M3.multiply(scaMat3, transforms);
    transforms = M3.multiply(rotMat3, transforms);
    transforms = M3.multiply(traMat3, transforms);
    transforms = M3.multiply(faceTransforms, transforms); // HEREDAR transformaciones de la cara

    uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms,
        u_color: objects.leftEye.color,
    }

    //Dibujamos el ojo izquierdo
    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(leftEyeVAO);
    twgl.drawBufferInfo(gl, leftEyeBufferInfo);

    //Para el ojo derecho
    //Primero aplicamos transformaciones locales del ojo (posición relativa)
    translate = [30, 30]; // Posición relativa a la cara
    angle_radians = objects.rightEye.rr.z;
    scale = [objects.rightEye.s.x, objects.rightEye.s.y];

    const scaMat4 = M3.scale(scale);
    const rotMat4 = M3.rotation(angle_radians);
    const traMat4 = M3.translation(translate);

    //HAcemos la escala, luego rotación y al final traslación
    transforms = M3.identity();
    transforms = M3.multiply(scaMat4, transforms);
    transforms = M3.multiply(rotMat4, transforms);
    transforms = M3.multiply(traMat4, transforms);
    transforms = M3.multiply(faceTransforms, transforms); 

    uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms,
        u_color: objects.rightEye.color,
    }

    //Dibujamos el ojo derecho
    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(rightEyeVAO);
    twgl.drawBufferInfo(gl, rightEyeBufferInfo);

    //Para la boca
    //Primero aplicamos transformaciones locales de la boca (posición relativa)
    translate = [0, 10]; // Posición relativa a la cara
    angle_radians = objects.mouth.rr.z;
    scale = [objects.mouth.s.x, objects.mouth.s.y];

    const scaMat5 = M3.scale(scale);
    const rotMat5 = M3.rotation(angle_radians);
    const traMat5 = M3.translation(translate);

    //HAcemos la escala, luego rotación y al final traslación
    transforms = M3.identity();
    transforms = M3.multiply(scaMat5, transforms);
    transforms = M3.multiply(rotMat5, transforms);
    transforms = M3.multiply(traMat5, transforms);
    transforms = M3.multiply(faceTransforms, transforms); // HEREDAR transformaciones de la cara
    uniforms = {
        u_resolution: [gl.canvas.width, gl.canvas.height],
        u_transforms: transforms,
        u_color: objects.mouth.color,
    }

    //Dibujamos la boca
    twgl.setUniforms(programInfo, uniforms);
    gl.bindVertexArray(mouthVAO);
    twgl.drawBufferInfo(gl, mouthBufferInfo);

    //Llamar de nuevo a drawScene en el siguiente frame
    requestAnimationFrame(() => drawScene(gl, pivotVAO, faceVAO, leftEyeVAO, rightEyeVAO, mouthVAO, programInfo, pivotBufferInfo, faceBufferInfo, leftEyeBufferInfo, rightEyeBufferInfo, mouthBufferInfo));
}

function setupUI(gl) {
    const gui = new GUI();

    // Controles del PIVOT
    const pivotFolder = gui.addFolder('Pivot');
    const pivotTranslationFolder = pivotFolder.addFolder('Translation');
    pivotTranslationFolder.add(objects.pivot.t, 'x', 0, gl.canvas.width);
    pivotTranslationFolder.add(objects.pivot.t, 'y', 0, gl.canvas.height);
    
    const PivotcolorFolder = pivotFolder.addFolder('Color');
    PivotcolorFolder.addColor(objects.pivot, 'color');

    // Controles de la CARA
    const faceFolder = gui.addFolder('Face');

    const traFolder = faceFolder.addFolder('Translation');
    traFolder.add(objects.face.t, 'x', 0, gl.canvas.width);
    traFolder.add(objects.face.t, 'y', 0, gl.canvas.height);

    const rotFolder = faceFolder.addFolder('Rotation');
    rotFolder.add(objects.face.rr, 'z', 0, Math.PI * 2);

    const scaleFolder = faceFolder.addFolder('Scale');
    scaleFolder.add(objects.face.s, 'x', 0.1, 3);
    scaleFolder.add(objects.face.s, 'y', 0.1, 3);

    const colorFolder = faceFolder.addFolder('Color');
    colorFolder.addColor(objects.leftEye, 'color').name('Eyes').onChange((value) => {
        objects.rightEye.color = value;
        objects.mouth.color = value;
    });
}

// Create the data for the vertices of the polyton, as an object with two arrays
function generateData(sides, centerX, centerY, radius) {
    // The arrays are initially empty
    let arrays =
    {
        // Two components for each position in 2D
        a_position: { numComponents: 2, data: [] },
        // Three components for each triangle, the 3 vertices
        indices: { numComponents: 3, data: [] }
    };

    // Initialize the center vertex, at the origin and with white color
    arrays.a_position.data.push(centerX);
    arrays.a_position.data.push(centerY);

    let angleStep = 2 * Math.PI / sides;
    // Loop over the sides to create the rest of the vertices
    for (let s = 0; s < sides; s++) {
        let angle = angleStep * s;
        // Generate the coordinates of the vertex
        let x = centerX + Math.cos(angle) * radius;
        let y = centerY + Math.sin(angle) * radius;
        arrays.a_position.data.push(x);
        arrays.a_position.data.push(y);

        // Define the triangles, in counter clockwise order
        arrays.indices.data.push(0);
        arrays.indices.data.push(s + 1);
        arrays.indices.data.push(((s + 2) <= sides) ? (s + 2) : 1);
    }
    console.log(arrays);

    return arrays;
}

main()