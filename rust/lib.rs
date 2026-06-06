use pyo3::prelude::*;
use pgn_reader::{Visitor, BufferedReader, SanPlus, Skip};
use shakmaty::{Chess, Position, Outcome, Move, Role, zobrist::{ZobristHash, Zobrist64}};
use std::collections::HashMap;

const NO_PLY_LIMIT: usize = usize::MAX;

#[inline]
fn encode_move(m: &Move) -> u32 {
    let role_index = |r: Role| -> u32 {
        match r {
            Role::Pawn   => 1,
            Role::Knight => 2,
            Role::Bishop => 3,
            Role::Rook   => 4,
            Role::Queen  => 5,
            Role::King   => 6,
        }
    };

    match m {
        Move::Normal { from, to, promotion, .. } => {
            let promo = promotion.map(role_index).unwrap_or(0);
            (*from as u32) | ((*to as u32) << 6) | (promo << 12)
        }
        Move::EnPassant { from, to } => {
            (*from as u32) | ((*to as u32) << 6)
        }
        Move::Castle { king, rook } => {
            (*king as u32) | ((*rook as u32) << 6) | (1 << 15)
        }
        Move::Put { to, role } => {
            ((*to as u32) << 6) | (role_index(*role) << 12) | (2 << 15)
        }
    }
}

type MoveStats = HashMap<(i64, u32), (u32, u32, u32)>;

struct GameParser {
    board: Chess,
    moves: Vec<(i64, u32)>,
    ply: usize,
    max_plies: usize,
    outcome: Option<Outcome>,
    stats: MoveStats,
}

impl GameParser {
    fn new(max_plies: usize) -> Self {
        Self {
            board: Chess::default(),
            moves: Vec::new(),
            ply: 0,
            max_plies,
            outcome: None,
            stats: HashMap::new(),
        }
    }
}

impl Visitor for GameParser {
    type Result = ();

    fn begin_game(&mut self) {
        self.board = Chess::default();
        self.moves.clear();
        self.ply = 0;
        self.outcome = None;
    }

    fn san(&mut self, san_plus: SanPlus) {
        if self.ply >= self.max_plies {
            return;
        }
        if let Ok(m) = san_plus.san.to_move(&self.board) {
            let hash: Zobrist64 = self.board.zobrist_hash(shakmaty::EnPassantMode::Legal);
            self.moves.push((hash.0 as i64, encode_move(&m)));
            self.board.play_unchecked(&m);
            self.ply += 1;
        }
    }

    fn outcome(&mut self, outcome: Option<Outcome>) {
        self.outcome = outcome;
    }

    fn end_game(&mut self) -> Self::Result {
        for (hash, mv) in self.moves.drain(..) {
            let entry = self.stats.entry((hash, mv)).or_insert((0, 0, 0));
            match self.outcome {
                Some(Outcome::Decisive { winner: shakmaty::Color::White }) => entry.0 += 1,
                Some(Outcome::Draw) => entry.1 += 1,
                Some(Outcome::Decisive { winner: shakmaty::Color::Black }) => entry.2 += 1,
                None => {}
            }
        }
    }

    fn begin_variation(&mut self) -> Skip {
        Skip(true)
    }
}

#[pyfunction]
#[pyo3(signature = (pgn_path, csv_path, max_plies=None))]
fn parse_pgn(
    pgn_path: &str,
    csv_path: &str,
    max_plies: Option<usize>,
) -> PyResult<()> {
    let file = std::fs::File::open(pgn_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    let mut buffered = BufferedReader::new(file);
    let mut visitor = GameParser::new(max_plies.unwrap_or(NO_PLY_LIMIT));

    loop {
        match buffered.read_game(&mut visitor) {
            Ok(Some(_)) => {}
            Ok(None) => break,
            Err(e) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    e.to_string(),
                ))
            }
        }
    }

    let mut wtr = csv::Writer::from_path(csv_path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

    for ((hash, mv), (wins, draws, losses)) in &visitor.stats {
        wtr.write_record(&[
            hash.to_string(), mv.to_string(),
            wins.to_string(), draws.to_string(), losses.to_string(),
        ]).map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    }
    wtr.flush().map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

    Ok(())
}

#[pymodule]
fn shakmaty_python(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_pgn, m)?)?;
    Ok(())
}
