export const LEVEL_COUNT = 10;
export const CHUNKS_PER_LEVEL = 20;

const chunkCache = new Map();

function pad(value, length) {
    return String(value).padStart(length, "0");
}

export function randomInteger(maximum) {
    if (!Number.isInteger(maximum) || maximum < 1) {
        throw new RangeError("The random range must contain at least one value.");
    }

    const limit = Math.floor(0x100000000 / maximum) * maximum;
    const values = new Uint32Array(1);

    do {
        crypto.getRandomValues(values);
    } while (values[0] >= limit);

    return values[0] % maximum;
}

export function getChunkPath(level, chunk) {
    if (!Number.isInteger(level) || level < 1 || level > LEVEL_COUNT) {
        throw new RangeError(`Difficulty must be between 1 and ${LEVEL_COUNT}.`);
    }

    if (!Number.isInteger(chunk) || chunk < 1 || chunk > CHUNKS_PER_LEVEL) {
        throw new RangeError(`Chunk must be between 1 and ${CHUNKS_PER_LEVEL}.`);
    }

    return `data/level-${pad(level, 2)}/boards-${pad(chunk, 4)}.json.gz`;
}

async function decodeResponse(response) {
    const buffer = await response.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    const isGzip = bytes.length >= 2 && bytes[0] === 0x1f && bytes[1] === 0x8b;

    if (!isGzip) {
        return new TextDecoder("utf-8").decode(bytes);
    }

    if (!("DecompressionStream" in window)) {
        throw new Error("This browser cannot decompress the Sudoku data files.");
    }

    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return new Response(stream).text();
}

function validateBoard(record, position, path) {
    if (!Array.isArray(record) || record.length !== 2) {
        throw new Error(`${path} contains an invalid board at position ${position + 1}.`);
    }

    const [puzzle, solution] = record;

    if (!/^\d{81}$/.test(puzzle) || !/^[1-9]{81}$/.test(solution)) {
        throw new Error(`${path} contains invalid puzzle data at position ${position + 1}.`);
    }

    for (let index = 0; index < 81; index += 1) {
        if (puzzle[index] !== "0" && puzzle[index] !== solution[index]) {
            throw new Error(`${path} contains a puzzle that does not match its solution at position ${position + 1}.`);
        }
    }
}

function validateChunk(data, path) {
    if (!Array.isArray(data) || data.length === 0) {
        throw new Error(`${path} does not contain any boards.`);
    }

    data.forEach((record, position) => validateBoard(record, position, path));
    return data;
}

export async function loadChunk(level, chunk) {
    const path = getChunkPath(level, chunk);

    if (!chunkCache.has(path)) {
        const request = fetch(path, { cache: "default" })
            .then(async response => {
                if (!response.ok) {
                    throw new Error(`${path} returned HTTP ${response.status}.`);
                }

                const text = await decodeResponse(response);
                let data;

                try {
                    data = JSON.parse(text);
                } catch {
                    throw new Error(`${path} did not contain valid JSON after decompression.`);
                }

                return validateChunk(data, path);
            })
            .catch(error => {
                chunkCache.delete(path);
                throw error;
            });

        chunkCache.set(path, request);
    }

    return chunkCache.get(path);
}

export async function loadRandomBoard(level, excludedKey = "") {
    let selected = null;

    for (let attempt = 0; attempt < 6; attempt += 1) {
        const chunk = randomInteger(CHUNKS_PER_LEVEL) + 1;
        const boards = await loadChunk(level, chunk);
        const boardIndex = randomInteger(boards.length);
        const key = `${level}:${chunk}:${boardIndex}`;
        selected = { chunk, boards, boardIndex, key };

        if (key !== excludedKey) {
            break;
        }
    }

    const [puzzle, solution] = selected.boards[selected.boardIndex];

    return {
        level,
        chunk: selected.chunk,
        boardIndex: selected.boardIndex,
        boardCount: selected.boards.length,
        key: selected.key,
        path: getChunkPath(level, selected.chunk),
        puzzle,
        solution
    };
}
