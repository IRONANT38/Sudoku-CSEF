import { LEVEL_COUNT, loadRandomBoard, randomInteger } from "./board.js";

const SAVE_KEY = "mr-sudoku-current-game-v1";

const elements = {
    board: document.querySelector("#sudoku-board"),
    loading: document.querySelector("#loading-overlay"),
    status: document.querySelector("#status"),
    timer: document.querySelector("#timer"),
    currentLevel: document.querySelector("#current-level"),
    difficultyPanel: document.querySelector("#difficulty-panel"),
    difficultyButtons: document.querySelector("#difficulty-buttons"),
    changeDifficultyButton: document.querySelector("#change-difficulty-button"),
    closeDifficultyButton: document.querySelector("#close-difficulty-button"),
    notesButton: document.querySelector("#notes-button"),
    notesState: document.querySelector("#notes-state"),
    checkButton: document.querySelector("#check-button"),
    hintButton: document.querySelector("#hint-button"),
    resetButton: document.querySelector("#reset-button"),
    eraseButton: document.querySelector("#erase-button"),
    newGameButton: document.querySelector("#new-game-button"),
    installButton: document.querySelector("#install-button"),
    installDialog: document.querySelector("#install-dialog"),
    installInstructions: document.querySelector("#install-instructions"),
    winDialog: document.querySelector("#win-dialog"),
    winSummary: document.querySelector("#win-summary"),
    winCloseButton: document.querySelector("#win-close-button"),
    winNextButton: document.querySelector("#win-next-button")
};

const state = {
    level: 1,
    puzzle: "",
    solution: "",
    values: Array(81).fill(0),
    notes: Array.from({ length: 81 }, () => new Set()),
    selected: null,
    notesMode: false,
    errors: new Set(),
    correct: new Set(),
    hints: new Set(),
    completed: false,
    loading: true,
    source: null,
    startedAt: Date.now(),
    elapsedBeforeStart: 0
};

let installPrompt = null;
let timerInterval = null;
const cells = [];

function pushAnalytics(event, details = {}) {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event, ...details });
}

function isGiven(index) {
    return state.puzzle[index] !== "0";
}

function rowOf(index) {
    return Math.floor(index / 9);
}

function columnOf(index) {
    return index % 9;
}

function boxOf(index) {
    return Math.floor(rowOf(index) / 3) * 3 + Math.floor(columnOf(index) / 3);
}

function isPeer(first, second) {
    return rowOf(first) === rowOf(second)
        || columnOf(first) === columnOf(second)
        || boxOf(first) === boxOf(second);
}

function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function elapsedSeconds() {
    const activeSeconds = state.completed ? 0 : Math.floor((Date.now() - state.startedAt) / 1000);
    return state.elapsedBeforeStart + activeSeconds;
}

function updateTimer() {
    elements.timer.textContent = formatTime(elapsedSeconds());
}

function startTimer() {
    clearInterval(timerInterval);
    state.startedAt = Date.now();
    updateTimer();
    timerInterval = window.setInterval(updateTimer, 1000);
}

function stopTimer() {
    state.elapsedBeforeStart = elapsedSeconds();
    clearInterval(timerInterval);
    timerInterval = null;
    updateTimer();
}

function setStatus(message, type = "neutral") {
    elements.status.textContent = message;
    elements.status.dataset.type = type;
}

function setLoading(loading) {
    state.loading = loading;
    elements.loading.hidden = !loading;
    document.querySelectorAll(".control-panel button, .difficulty-buttons button").forEach(button => {
        button.disabled = loading;
    });
}

function serializeGame() {
    return {
        version: 1,
        level: state.level,
        puzzle: state.puzzle,
        solution: state.solution,
        values: state.values,
        notes: state.notes.map(notes => [...notes]),
        selected: state.selected,
        notesMode: state.notesMode,
        hints: [...state.hints],
        completed: state.completed,
        source: state.source,
        elapsedSeconds: elapsedSeconds()
    };
}

function saveGame() {
    if (!state.puzzle || state.loading) {
        return;
    }

    localStorage.setItem(SAVE_KEY, JSON.stringify(serializeGame()));
}

function restoreGame() {
    const savedText = localStorage.getItem(SAVE_KEY);

    if (!savedText) {
        return false;
    }

    try {
        const saved = JSON.parse(savedText);
        const valid = saved.version === 1
            && Number.isInteger(saved.level)
            && saved.level >= 1
            && saved.level <= LEVEL_COUNT
            && /^\d{81}$/.test(saved.puzzle)
            && /^[1-9]{81}$/.test(saved.solution)
            && Array.isArray(saved.values)
            && saved.values.length === 81
            && Array.isArray(saved.notes)
            && saved.notes.length === 81;

        if (!valid) {
            throw new Error("Invalid saved game");
        }

        state.level = saved.level;
        state.puzzle = saved.puzzle;
        state.solution = saved.solution;
        state.values = saved.values.map(value => Number(value) || 0);
        state.notes = saved.notes.map(notes => new Set(notes.filter(value => Number.isInteger(value) && value >= 1 && value <= 9)));
        state.selected = Number.isInteger(saved.selected) ? saved.selected : null;
        state.notesMode = Boolean(saved.notesMode);
        state.hints = new Set(Array.isArray(saved.hints) ? saved.hints : []);
        state.completed = Boolean(saved.completed);
        state.source = saved.source || null;
        state.elapsedBeforeStart = Number(saved.elapsedSeconds) || 0;
        state.loading = false;
        return true;
    } catch {
        localStorage.removeItem(SAVE_KEY);
        return false;
    }
}

function createBoard() {
    const fragment = document.createDocumentFragment();

    for (let index = 0; index < 81; index += 1) {
        const cell = document.createElement("button");
        const value = document.createElement("span");
        const notes = document.createElement("span");

        cell.type = "button";
        cell.className = "sudoku-cell";
        cell.dataset.index = String(index);
        cell.setAttribute("role", "gridcell");
        value.className = "cell-value";
        notes.className = "cell-notes";

        for (let number = 1; number <= 9; number += 1) {
            const note = document.createElement("span");
            note.dataset.note = String(number);
            notes.append(note);
        }

        cell.append(value, notes);
        cell.addEventListener("click", () => selectCell(index));
        cells.push(cell);
        fragment.append(cell);
    }

    elements.board.append(fragment);
}

function cellLabel(index) {
    const row = rowOf(index) + 1;
    const column = columnOf(index) + 1;
    const value = state.values[index];
    const notes = [...state.notes[index]].sort((a, b) => a - b);

    if (value) {
        return `Row ${row}, column ${column}, ${value}${isGiven(index) ? ", given clue" : ""}`;
    }

    if (notes.length) {
        return `Row ${row}, column ${column}, notes ${notes.join(", ")}`;
    }

    return `Row ${row}, column ${column}, empty`;
}

function renderBoard() {
    const selectedValue = state.selected === null ? 0 : state.values[state.selected];

    for (let index = 0; index < 81; index += 1) {
        const cell = cells[index];
        const valueElement = cell.querySelector(".cell-value");
        const noteElements = cell.querySelectorAll("[data-note]");
        const value = state.values[index];
        const selected = index === state.selected;
        const related = state.selected !== null && isPeer(index, state.selected);
        const matching = selectedValue !== 0 && value === selectedValue;

        cell.classList.toggle("given", state.puzzle && isGiven(index));
        cell.classList.toggle("selected", selected);
        cell.classList.toggle("related", related && !selected);
        cell.classList.toggle("matching", matching && !selected);
        cell.classList.toggle("error", state.errors.has(index));
        cell.classList.toggle("correct", state.correct.has(index));
        cell.classList.toggle("hinted", state.hints.has(index));
        cell.setAttribute("aria-selected", String(selected));
        cell.setAttribute("aria-readonly", String(state.puzzle ? isGiven(index) : true));
        cell.setAttribute("aria-label", state.puzzle ? cellLabel(index) : `Cell ${index + 1}`);

        valueElement.textContent = value ? String(value) : "";
        valueElement.hidden = value === 0;

        noteElements.forEach(note => {
            const number = Number(note.dataset.note);
            note.textContent = state.notes[index].has(number) && value === 0 ? String(number) : "";
        });
    }

    elements.notesButton.setAttribute("aria-pressed", String(state.notesMode));
    elements.notesButton.classList.toggle("active", state.notesMode);
    elements.notesState.textContent = state.notesMode ? "On" : "Off";
    elements.currentLevel.textContent = `Level ${state.level}`;
    elements.difficultyButtons.querySelectorAll("button").forEach(button => {
        const active = Number(button.dataset.level) === state.level;
        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "true" : "false");
    });

}

function selectCell(index) {
    if (state.loading || !state.puzzle) {
        return;
    }

    state.selected = index;
    renderBoard();
    cells[index].focus({ preventScroll: true });
}

function clearCheckMarks(index = null) {
    if (index === null) {
        state.errors.clear();
        state.correct.clear();
        return;
    }

    state.errors.delete(index);
    state.correct.delete(index);
}

function eliminatePeerNotes(index, number) {
    for (let other = 0; other < 81; other += 1) {
        if (other !== index && isPeer(index, other)) {
            state.notes[other].delete(number);
        }
    }
}

function enterNumber(number) {
    const index = state.selected;

    if (index === null || state.loading || state.completed || isGiven(index)) {
        return;
    }

    clearCheckMarks(index);
    state.hints.delete(index);

    if (state.notesMode) {
        if (state.values[index] !== 0) {
            return;
        }

        if (state.notes[index].has(number)) {
            state.notes[index].delete(number);
        } else {
            state.notes[index].add(number);
        }
    } else {
        state.values[index] = number;
        state.notes[index].clear();
        eliminatePeerNotes(index, number);
    }

    renderBoard();
    saveGame();
    checkVictory();
}

function eraseSelected() {
    const index = state.selected;

    if (index === null || state.loading || state.completed || isGiven(index)) {
        return;
    }

    state.values[index] = 0;
    state.notes[index].clear();
    state.hints.delete(index);
    clearCheckMarks(index);
    renderBoard();
    saveGame();
}

function toggleNotes() {
    if (state.loading || state.completed) {
        return;
    }

    state.notesMode = !state.notesMode;
    renderBoard();
    saveGame();
    setStatus(`Notes mode ${state.notesMode ? "on" : "off"}.`);
}

function checkBoard() {
    if (state.loading || state.completed) {
        return;
    }

    state.errors.clear();
    state.correct.clear();
    let filled = 0;

    for (let index = 0; index < 81; index += 1) {
        if (isGiven(index) || state.values[index] === 0) {
            continue;
        }

        filled += 1;

        if (state.values[index] === Number(state.solution[index])) {
            state.correct.add(index);
        } else {
            state.errors.add(index);
        }
    }

    renderBoard();

    if (state.errors.size) {
        setStatus(`${state.errors.size} incorrect ${state.errors.size === 1 ? "entry" : "entries"} highlighted.`, "error");
    } else if (filled) {
        setStatus("Everything entered so far is correct.", "success");
    } else {
        setStatus("Enter a few numbers before checking the board.");
    }

    pushAnalytics("sudoku_check", { difficulty: state.level, incorrect_entries: state.errors.size });
}

function giveHint() {
    if (state.loading || state.completed) {
        return;
    }

    const candidates = [];

    for (let index = 0; index < 81; index += 1) {
        if (!isGiven(index) && state.values[index] !== Number(state.solution[index])) {
            candidates.push(index);
        }
    }

    if (!candidates.length) {
        setStatus("No hint is available.");
        return;
    }

    const index = candidates[randomInteger(candidates.length)];
    const number = Number(state.solution[index]);
    state.values[index] = number;
    state.notes[index].clear();
    state.hints.add(index);
    state.selected = index;
    clearCheckMarks(index);
    eliminatePeerNotes(index, number);
    renderBoard();
    saveGame();
    setStatus(`Hint filled row ${rowOf(index) + 1}, column ${columnOf(index) + 1}.`, "hint");
    pushAnalytics("sudoku_hint", { difficulty: state.level });
    checkVictory();
}

function resetPuzzle() {
    if (state.loading || !state.puzzle) {
        return;
    }

    const hasProgress = state.values.some((value, index) => !isGiven(index) && value !== 0)
        || state.notes.some(notes => notes.size > 0);

    if (hasProgress && !window.confirm("Reset every entry and note on this puzzle?")) {
        return;
    }

    state.values = [...state.puzzle].map(value => Number(value));
    state.notes = Array.from({ length: 81 }, () => new Set());
    state.errors.clear();
    state.correct.clear();
    state.hints.clear();
    state.completed = false;
    state.selected = state.values.findIndex(value => value === 0);
    state.elapsedBeforeStart = 0;
    startTimer();
    renderBoard();
    saveGame();
    setStatus("Puzzle reset.");
    pushAnalytics("sudoku_reset", { difficulty: state.level });
}

function applyLoadedBoard(board) {
    state.level = board.level;
    state.puzzle = board.puzzle;
    state.solution = board.solution;
    state.values = [...board.puzzle].map(value => Number(value));
    state.notes = Array.from({ length: 81 }, () => new Set());
    state.selected = state.values.findIndex(value => value === 0);
    state.notesMode = false;
    state.errors.clear();
    state.correct.clear();
    state.hints.clear();
    state.completed = false;
    state.source = {
        chunk: board.chunk,
        boardIndex: board.boardIndex,
        boardCount: board.boardCount,
        key: board.key,
        path: board.path
    };
    state.elapsedBeforeStart = 0;
}

function setDifficultyOpen(open) {
    elements.difficultyPanel.hidden = !open;
    elements.changeDifficultyButton.setAttribute("aria-expanded", String(open));

    if (open) {
        const activeButton = elements.difficultyButtons.querySelector(`[data-level="${state.level}"]`);
        requestAnimationFrame(() => activeButton?.focus());
    }
}

function toggleDifficulty() {
    setDifficultyOpen(elements.difficultyPanel.hidden);
}

async function newGame(level = state.level) {
    if (state.loading) {
        return;
    }

    setLoading(true);
    setStatus(`Loading a Level ${level} puzzle…`);
    elements.currentLevel.textContent = `Level ${level}`;
    const previousKey = state.source?.key || "";

    try {
        const board = await loadRandomBoard(level, previousKey);
        applyLoadedBoard(board);
        startTimer();
        renderBoard();
        setLoading(false);
        saveGame();
        setDifficultyOpen(false);
        setStatus(`Level ${level} puzzle ready. Choose a cell and start solving.`, "success");
        pushAnalytics("sudoku_new_game", { difficulty: level, chunk: board.chunk });
        requestAnimationFrame(() => cells[state.selected]?.focus({ preventScroll: true }));
    } catch (error) {
        setStatus(error instanceof Error ? error.message : String(error), "error");
        console.error(error);
    } finally {
        if (state.loading) {
            setLoading(false);
        }
    }
}

function checkVictory() {
    if (!state.solution || state.completed) {
        return false;
    }

    const solved = state.values.every((value, index) => value === Number(state.solution[index]));

    if (!solved) {
        return false;
    }

    stopTimer();
    state.completed = true;
    state.errors.clear();
    state.correct = new Set(Array.from({ length: 81 }, (_, index) => index).filter(index => !isGiven(index)));
    renderBoard();
    saveGame();
    elements.winSummary.textContent = `Level ${state.level} completed in ${formatTime(state.elapsedBeforeStart)}.`;
    elements.winDialog.showModal();
    setStatus("Puzzle complete!", "success");
    pushAnalytics("sudoku_complete", { difficulty: state.level, elapsed_seconds: state.elapsedBeforeStart });
    return true;
}

function moveSelection(key) {
    if (state.selected === null) {
        state.selected = 0;
    }

    let row = rowOf(state.selected);
    let column = columnOf(state.selected);

    if (key === "ArrowUp") row = (row + 8) % 9;
    if (key === "ArrowDown") row = (row + 1) % 9;
    if (key === "ArrowLeft") column = (column + 8) % 9;
    if (key === "ArrowRight") column = (column + 1) % 9;

    selectCell(row * 9 + column);
}

function handleKeyboard(event) {
    if (event.key === "Escape" && !elements.difficultyPanel.hidden) {
        setDifficultyOpen(false);
        elements.changeDifficultyButton.focus();
        return;
    }

    if (elements.installDialog.open || elements.winDialog.open || !elements.difficultyPanel.hidden) {
        return;
    }

    if (/^[1-9]$/.test(event.key)) {
        event.preventDefault();
        enterNumber(Number(event.key));
        return;
    }

    if (["Backspace", "Delete", "0"].includes(event.key)) {
        event.preventDefault();
        eraseSelected();
        return;
    }

    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        moveSelection(event.key);
        return;
    }

    if (event.key.toLowerCase() === "n") toggleNotes();
    if (event.key.toLowerCase() === "c") checkBoard();
    if (event.key.toLowerCase() === "h") giveHint();
}

function createDifficultyButtons() {
    const fragment = document.createDocumentFragment();

    for (let level = 1; level <= LEVEL_COUNT; level += 1) {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.level = String(level);
        button.textContent = String(level);
        button.setAttribute("aria-label", `Start a Level ${level} puzzle`);
        button.addEventListener("click", () => newGame(level));
        fragment.append(button);
    }

    elements.difficultyButtons.append(fragment);
}

function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
}

function isIOS() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent)
        || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

async function installApp() {
    if (isStandalone()) {
        setStatus("Mr. Sudoku is already installed on this device.", "success");
        return;
    }

    if (installPrompt) {
        installPrompt.prompt();
        const choice = await installPrompt.userChoice;
        pushAnalytics("pwa_install_choice", { outcome: choice.outcome });
        installPrompt = null;
        return;
    }

    if (isIOS()) {
        elements.installInstructions.textContent = "Open the browser's Share menu, then choose Add to Home Screen. Mr. Sudoku will open from its own icon like an app.";
    } else {
        elements.installInstructions.textContent = "Open your browser menu and choose Install Mr. Sudoku, Install app, or Create shortcut. Supported desktop browsers can open it in its own app window.";
    }

    elements.installDialog.showModal();
}

function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) {
        return;
    }

    window.addEventListener("load", () => {
        navigator.serviceWorker.register("./service-worker.js").catch(error => console.error(error));
    });
}

function setupEvents() {
    document.querySelectorAll("[data-number]").forEach(button => {
        button.addEventListener("click", () => enterNumber(Number(button.dataset.number)));
    });

    elements.eraseButton.addEventListener("click", eraseSelected);
    elements.notesButton.addEventListener("click", toggleNotes);
    elements.checkButton.addEventListener("click", checkBoard);
    elements.hintButton.addEventListener("click", giveHint);
    elements.resetButton.addEventListener("click", resetPuzzle);
    elements.newGameButton.addEventListener("click", () => newGame());
    elements.changeDifficultyButton.addEventListener("click", toggleDifficulty);
    elements.closeDifficultyButton.addEventListener("click", () => {
        setDifficultyOpen(false);
        elements.changeDifficultyButton.focus();
    });
    elements.installButton.addEventListener("click", installApp);
    elements.winCloseButton.addEventListener("click", () => elements.winDialog.close());
    elements.winNextButton.addEventListener("click", () => {
        elements.winDialog.close();
        newGame();
    });
    document.addEventListener("keydown", handleKeyboard);

    window.addEventListener("beforeinstallprompt", event => {
        event.preventDefault();
        installPrompt = event;
        elements.installButton.hidden = false;
    });

    window.addEventListener("appinstalled", () => {
        installPrompt = null;
        elements.installButton.hidden = true;
        setStatus("Mr. Sudoku was installed successfully.", "success");
        pushAnalytics("pwa_installed");
    });

    window.addEventListener("offline", () => setStatus("You are offline. Previously loaded game files remain available."));
    window.addEventListener("online", () => setStatus("Back online.", "success"));
    window.addEventListener("pagehide", saveGame);
}

async function initialize() {
    createBoard();
    createDifficultyButtons();
    setupEvents();
    registerServiceWorker();

    if (isStandalone()) {
        elements.installButton.hidden = true;
    }

    if (restoreGame()) {
        setLoading(false);
        renderBoard();

        if (state.completed) {
            updateTimer();
            setStatus("Completed puzzle restored.", "success");
        } else {
            startTimer();
            setStatus("Your previous puzzle was restored.", "success");
        }

        return;
    }

    state.loading = false;
    await newGame(1);
}

initialize();
