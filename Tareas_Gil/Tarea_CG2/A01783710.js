/*
    Tarea CG2 - Generador de Edificios en Formato OBJ
    Aquiba Yudah Benarroch Bitton A01783710

 */

import fs from 'fs'; // Para poder crear el archivo OBJ
import { V3 }  from './A01783710_3d-lib.js';

/*  Primero se deben leer los argumentos de la línea de comandos
    Se leen los argumentos de la línea de comandos
    Primero se debe poner node A01783710.js <lados> <altura> <radioBase> <radioCima>
    En caso de ser uno o mas niveles adicionales, se deben agregar los siguientes argumentos:
    <alturaNivel1> <radioBaseNivel1> <radioCimaNivel1> ... <alturaNivelN> <radioBaseNivelN> <radioCimaNivelN>
    Ejemplo: node A01783710.js 8 6.0 1.0 0.8
    Ejemplo con dos niveles: node A01783710.js 8 6.0 1.0 0.8 2 4.0 0.8 0.8 3.0 0.6 0.6
    Si no se proporcionan argumentos, se usan valores por defecto:
    lados = 8, altura = 6.0, radioBase = 1.0, radioCima = 0.8, niveles = 0
*/

//Se leen los argumentos de la linea de comando. Usamos parseInt y parseFloat para convertirlos a números.
function parseArguments() {
    const args = process.argv.slice(2);
    
    // Valores por defecto
    let sides = args[0] ? parseInt(args[0]) : 8;
    let height = args[1] ? parseFloat(args[1]) : 6.0;
    let radiusBottom = args[2] ? parseFloat(args[2]) : 1.0;
    let radiusTop = args[3] ? parseFloat(args[3]) : 0.8;
    
    //Para diferentes niveles
    let levels = args[4] ? parseInt(args[4]) : 0;
    

    // Validación de los lados, radios y altura
    if (sides < 3 || sides > 36) {
        console.error('El número de lados debe estar entre 3 y 36');
        //Sale del proceso
        process.exit(1);
    }
    
    // Validar que la altura y los radios sean positivos
    if (height <= 0 || radiusBottom <= 0 || radiusTop <= 0) {
        console.error('La altura y los radios deben ser positivos');
        process.exit(1);
    }

    // Construir el arreglo de niveles si es necesario
    let levelArray = [];
    levelArray.push({
        height: height,
        radiusBottom: radiusBottom,
        radiusTop: radiusTop
    });

    if (levels > 0) {
        // Validar que haya suficientes argumentos para los niveles, y en caso dado de que hayan mas, imprimir un error.
        const expectedArguments = 5 + levels * 3;
        if (args.length < expectedArguments) {
            console.error('No se han proporcionado suficientes argumentos para los niveles especificados.');
            process.exit(1);
        }
        if(args.length > expectedArguments) {
            console.error('Se han proporcionado más argumentos de los necesarios para los niveles especificados.');
            process.exit(1);
        }
        // Obtenemos los valores para cada nivel adicional
        for (let i = 0; i < levels; i++) {
            let levelHeight = args[5 + i * 3] ? parseFloat(args[5 + i * 3]) : null;
            let levelRadiusBottom = args[6 + i * 3] ? parseFloat(args[6 + i * 3]) : null;
            let levelRadiusTop = args[7 + i * 3] ? parseFloat(args[7 + i * 3]) : null;

            if (levelHeight === null || levelRadiusBottom === null || levelRadiusTop === null) {
                console.error(`Faltan argumentos para el nivel ${i + 1}.`);
                process.exit(1);
            }
            levelArray.push({
                height: levelHeight,
                radiusBottom: levelRadiusBottom,
                radiusTop: levelRadiusTop
            });
        }
    }

    return { sides, height, radiusBottom, radiusTop, levels, levelArray};
}

// Generar vértices para los niveles
// Parametros: 
// - sides: número de lados del polígono
// - levelArray: arreglo de niveles con sus propiedades


function generateVertices(sides, levelArray) {
    let vertices = [];
    // Ángulo entre cada lado del polígono
    let angleStep = (2 * Math.PI) / sides;
    
    let currentHeight = 0; // Altura acumulada para cada nivel

    // Para cada nivel generamos: centro base, círculo base, centro cima, círculo cima
    for (let i = 0; i < levelArray.length; i++) {
        let level = levelArray[i];

        // Centro del círculo BASE
        vertices.push({ x: 0, y: currentHeight, z: 0 });

        // Vértices del círculo BASE
        for (let j = 0; j < sides; j++) {
            const angle = j * angleStep;
            vertices.push({ 
                x: level.radiusBottom * Math.cos(angle),
                y: currentHeight,
                z: level.radiusBottom * Math.sin(angle)
            });
        }

        // Centro del círculo CIMA
        vertices.push({ x: 0, y: currentHeight + level.height, z: 0 });

        // Vértices del círculo CIMA
        for (let j = 0; j < sides; j++) {
            const angle = j * angleStep;
            vertices.push({ 
                x: level.radiusTop * Math.cos(angle),
                y: currentHeight + level.height,
                z: level.radiusTop * Math.sin(angle)
            });
        }

        // Actualizar la altura para el próximo nivel
        currentHeight += level.height;
    }
    
    return vertices;
}

// Generar caras triangulares para múltiples niveles
// Esta función crea todas las caras
// sides: número de lados del polígono
// numLevels: cantidad de niveles del edificio

/* 
    Para la funcion de generateFaces, se utilizo IA (Cloude AI) para el desarrollo y el 
    funcionamiento correcto. Sin embargo, el codigo fue adaptado y modificado por mi para cumplir 
    con la tarea, explicar bien el funcionamiento y que no sea solamente un copy paste.
*/
function generateFaces(sides, numLevels) {
    let faces = [];

    // Cuantos verticaes hay por nivel
    // Se calcula 2 porque tenemos base y top, y el 2*sides es por los vértices de cada círculo
    // Centro de la base, circulo base, centro top, círculo top
    let verticesPerLevel = 2 + 2 * sides;

    // Iterar sobre cada nivel 
    for (let i = 0; i < numLevels; i++) {
        // indiceInicial: índice donde comienzan los vértices de este nivel
        // Al multiplicar i * verticesPerLevel, obtenemos la posicion incial de este nivel
        let indiceInicial = i * verticesPerLevel;

        // centerBottom: índice del centro en la base de este nivel
        // Es el primer vértice del nivel actual
        let centerBottom = indiceInicial;
        
        // centerTop: índice del centro en la cima de este nivel
        // Está ubicado después del centro base + todos los vértices del círculo base
        let centerTop = indiceInicial + sides + 1;

        // Si estamos en el primer nivel, creamos la base
        if (i === 0) {
            // Crear un triángulo por cada lado del polígono
            for (let i = 0; i < sides; i++) {
                // Vértice actual del círculo base
                // Suma i+1 porque el centro está en indiceInicial y los vertices empiezan en indiceInicial+1
                let current = indiceInicial + i + 1;
                
                // Siguiente vértice del círculo
                let next;
                if (i === sides - 1) {
                    next = indiceInicial + 1; // Volver al primer vértice
                } else {
                    next = indiceInicial + i + 2; //Siguiente vertice
                }

                // Se crea el triángulo
                // Lo ponemos en este orden porque la normal debe apuntar hacia afuera
                faces.push({
                    vertices: [centerBottom, next, current],
                    type: 'bottom'
                });
            }
        }

        // Para las caras laterales
        // Concetan el círculo base con el que está arriba del mismo nivel
        // Se hace por medio de dos triángulos por cada lado (lo que forma un cuadrado)
        for (let j = 0; j < sides; j++) {
            // Vértices del círculo base
            let bottomCurrent = indiceInicial + j + 1;
            let bottomNext;
            if (j === sides - 1) {
                bottomNext = indiceInicial + 1;
            } else {
                bottomNext = indiceInicial + j + 2;
            }
            
            // Vértices del círculo de arriba del nivel
            // Hay que sumar sides para ignorar el centro base y los vértices base
            let topCurrent = indiceInicial + sides + 2 + j;
            let topNext;
            if (j === sides - 1) {
                topNext = indiceInicial + sides + 2;
            } else {
                topNext = indiceInicial + sides + 2 + j + 1;
            }

            // Primer triángulo del cuadrado lateral
            faces.push({
                vertices: [bottomCurrent, topCurrent, bottomNext],
                type: 'side'
            });

            // Segundo triángulo del cuadrado lateral
            faces.push({
                vertices: [bottomNext, topCurrent, topNext],
                type: 'side'
            });
        }

        // PAra la cima
        // Solo se crean para el último nivel
        if (i === numLevels - 1) {
            // Crear un triángulo por cada lado del polígono superior
            for (let j = 0; j < sides; j++) {
                // Vértice actual del círculo superior
                let current = indiceInicial + sides + 2 + j;
                
                // Siguiente vértice del círculo superior
                let next;
                if (j === sides - 1) {
                    next = indiceInicial + sides + 2;
                }
                else {
                    next = indiceInicial + sides + 2 + j + 1;
                }

                // Crear triángulo
                faces.push({
                    vertices: [centerTop, current, next],
                    type: 'top'
                });
            }
        }
    }

    return faces;
}

// Calcular vector normal para un vértice usando V3
// Primero se crean vectores para los tres vértices
// Despues se crean los vectores de los lados restando los vectores de los vértices
// Finalmente se calcula el producto cruz y se normaliza
function calculateNormal(v1, v2, v3) {
    // Convertir vértices a vectores V3
    const vec1 = V3.create(v1.x, v1.y, v1.z);
    const vec2 = V3.create(v2.x, v2.y, v2.z);
    const vec3 = V3.create(v3.x, v3.y, v3.z);
    
    // Vector del primer lado: v2 - v1 
    const side1 = V3.subtract(vec2, vec1);
    
    // Vector del segundo lado: v3 - v1
    const side2 = V3.subtract(vec3, vec1);
    
    // Producto cruz: side1 × side2
    const crossProduct = V3.cross(side1, side2);
    
    // Normalizar
    const normalizedVector = V3.normalize(crossProduct);

    return {
        x: normalizedVector[0],
        y: normalizedVector[1],
        z: normalizedVector[2]
    };
}

// Generar todas las normales para las caras
function generateNormals(vertices, faces) {
    const normals = [];
    
    for (const face of faces) {
        const v1 = vertices[face.vertices[0]];
        const v2 = vertices[face.vertices[1]];
        const v3 = vertices[face.vertices[2]];
        
        const normal = calculateNormal(v1, v2, v3);
        normals.push(normal);
    }
    
    return normals;
}

// Escribir archivo OBJ
function writeOBJFile(fileName, vertices, normals, allFaces) {
    const lines = [];

    // Vertices
    lines.push(`# ${vertices.length} vertices`);
    // Escribir vértices en formato x y z
    for (let v of vertices) {
        lines.push(`v ${v.x.toFixed(4)} ${v.y.toFixed(4)} ${v.z.toFixed(4)}`);
    }

    // Normales
    lines.push(`# ${normals.length} normales`);
    for (let n of normals) {
        lines.push(`vn ${n.x.toFixed(4)} ${n.y.toFixed(4)} ${n.z.toFixed(4)}`);
    }

    // Caras
    lines.push(`# ${allFaces.length} caras`);
    for (let i = 0; i < allFaces.length; i++) {
        const face = allFaces[i];
        const normalIdx = i + 1;
        const v1 = face.vertices[0] + 1;
        const v2 = face.vertices[1] + 1;
        const v3 = face.vertices[2] + 1;
        lines.push(`f ${v1}//${normalIdx} ${v2}//${normalIdx} ${v3}//${normalIdx}`);
    }
    
    // Guardar archivo
    fs.writeFileSync(fileName, lines.join('\n'));
    console.log(`Archivo OBJ guardado como ${fileName}`);
}

// Función principal
function main() {
    // Leer argumentos de línea de comandos
    const { sides, levelArray } = parseArguments();

    // Generar geometría del edificio
    const vertices = generateVertices(sides, levelArray);
    const allFaces = generateFaces(sides, levelArray.length);
    const normals = generateNormals(vertices, allFaces);

    // Crear archivo OBJ
    const firstLevel = levelArray[0];
    const fileName = `building_${sides}_${firstLevel.height}_${firstLevel.radiusBottom}_${firstLevel.radiusTop}.obj`;

    //Escribe y guarda el archivo
    writeOBJFile(fileName, vertices, normals, allFaces);

}

// Ejecutar programa
main();
