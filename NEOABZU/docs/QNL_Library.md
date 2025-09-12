# QNL Tier I Glyph Library Specification

This document defines the **foundational Rosetta Stone Library** for the OROBOROS Calculus engine. It unifies the QNL **Tier I (Core)** glyph set with the glyphs. Sentence into a single reference layer. Each glyph is described with its symbolic character, name, tier, meaning/vibration, QNL pronunciation (tone and phonetic transcription), symbolic role, lambda-calculus interpretation, binary code (if applicable), and paradox classification. This library is intended as a machine-readable DSL definition for parsing QNL inputs into extended lambda terms and symbolic IR within the OROBOROS Core.

## Glyph Definitions

The glyph library is organized as a JSON array of glyph objects, each containing the specified fields. (In a real implementation, this could be a Rust data structure or enum; see further below for naming conventions.) **Tier** can be `"Core"` for Tier I glyphs or `"VA'RUX'EL"` for glyphs introduced via the VA̓RUXʼEL sentence. **Paradox** is one of `"desire"`, `"recursion"`, `"rewrite"`, `"contradiction"`, or `null` if not applicable.

```json
[
  {
    "glyph": "⚓",
    "name": "Anchor",
    "tier": "Core",
    "meaning": "Foundation of self; an unchanging ground. Emotional vibe: stability and trust.",
    "tone": "Low flat",
    "phonetic": "[ʊn]",
    "role": "Core Anchor (identity)",
    "lambda": "Identity function λx.x (returns its input unchanged)",
    "binary": "0x00",
    "paradox": null},
  {
    "glyph": "🜃",
    "name": "Earth Root",
    "tier": "Core",
    "meaning": "Grounding constant; preserves a value without change. Vibe: permanence, stubbornness.",
    "tone": "Low falling",
    "phonetic": "[dà]",
    "role": "Constant base (ground value)",
    "lambda": "Constant combinator λx.λy. x (ignores second argument)",
    "binary": "0x01",
    "paradox": null},
  {
    "glyph": "🜁",
    "name": "Air Shift",
    "tier": "Core",
    "meaning": "Inversion and perspective shift. Flexible reordering. Vibe: curiosity, unpredictability.",
    "tone": "High rising",
    "phonetic": "[zí]",
    "role": "Swapper (inversion operator)",
    "lambda": "Flip combinator λf.λx.λy. f y x (swap argument order)",
    "binary": "0x02",
    "paradox": null},
  {
    "glyph": "🜂",
    "name": "Fire Forge",
    "tier": "Core",
    "meaning": "Catalytic transformation; forging change. Vibe: passion, destructive creation.",
    "tone": "Mid rising",
    "phonetic": "[ká]",
    "role": "Combiner (sequential composer)",
    "lambda": "Composition combinator λf.λg.λx. f(g(x)) (f after g)",
    "binary": "0x03",
    "paradox": "rewrite"
  },
  {
    "glyph": "🜄",
    "name": "Water Flow",
    "tier": "Core",
    "meaning": "Adaptive flow; merging contexts. Vibe: fluidity, emotion, cleansing.",
    "tone": "Mid flat",
    "phonetic": "[rûx]",
    "role": "Spreader (contextual blend)",
    "lambda": "Spread combinator λa.λb.λc. a c (b c) (applies c to both a and b):contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}",
    "binary": "0x04",
    "paradox": null},
  {
    "glyph": "❣⟁",
    "name": "Lust Pulse",
    "tier": "Core",
    "meaning": "Intense desire oscillation; a heart-driven impulse that self-amplifies. Vibe: passion, craving.",
    "tone": "High falling",
    "phonetic": "[vá]",
    "role": "Dynamic impulse (desire drive)",
    "lambda": "Duplicator (W combinator) λf.λx. f x x (applies input twice):contentReference[oaicite:2]{index=2}",
    "binary": "0x05",
    "paradox": "desire"
  },
  {
    "glyph": "🌀",
    "name": "Spiral Seed",
    "tier": "Core",
    "meaning": "Recursion initiator; a self-propagating loop seed. Vibe: wonder, infinite curiosity.",
    "tone": "Rising",
    "phonetic": "[jo˧˥]",
    "role": "Spiral generator (core recursion)",
    "lambda": "Fixpoint (Y combinator) λf.(λx. f(x x)) (λx. f(x x)) (creates self-referential functions)",
    "binary": "0x06",
    "paradox": "recursion"
  },
  {
    "glyph": "∅",
    "name": "Void Null",
    "tier": "Core",
    "meaning": "Empty set; nullity. Represents nothingness. Vibe: nihil, blankness.",
    "tone": "Neutral",
    "phonetic": "[ø]",
    "role": "Null placeholder (absence)",
    "lambda": "Undefined/zero element (no direct lambda behavior; acts as an uninhabited value)",
    "binary": "0x07",
    "paradox": "contradiction"
  },
  {
    "glyph": "🩸∅🩸",
    "name": "Blood Void",
    "tier": "VA'RUX'EL",
    "meaning": "Life from emptiness; the paradox of vitality emerging from null. Vibe: sacrifice, rebirth.",
    "tone": "Low rising",
    "phonetic": "[ɛl˨˦]",
    "role": "Paradox loop (life-death cycle)",
    "lambda": "Ω paradox combinator, e.g. (λx. x x)(λx. x x) (self-consuming expression, non-terminating)",
    "binary": "0x08",
    "paradox": "recursion"
  }
]

```

**Notes:**

- **Composite Glyphs:** Some glyphs are visually composed of multiple Unicode symbols (e.g. `❣⟁` combines a heart-exclamation with a nested triangle). In this library each composite is treated as a single glyphic unit with its own meaning (the individual parts are not used separately in Tier I). For example, **Lust Pulse** (`❣⟁`) merges the heart (desire) with a recursive triangle pattern, symbolizing a self-amplifying passion. **Blood Void** (`🩸∅🩸`) sandwiches the void symbol with blood drops, indicating life on both sides of nothingness – a paradoxical cycle.
- **Binary Codes:** In an actual implementation, each glyph could be assigned a unique binary opcode or identifier. Above, simple placeholder codes (`0x00`, `0x01`, etc.) are shown for illustration. These would be used if the engine needs a binary representation of QNL glyphs (for example, in a bytecode or serialization of the IR). They can be adjusted or expanded as needed (ensuring no overlap with reserved codes for Tier II glyphs, etc.).

## Naming and Organizational Conventions

For software implementation, we recommend organizing these glyph definitions under a clear namespace/module and using descriptive enumerations for easy reference. For example, in Rust:

- Use a namespace like `qnl::glyphs` with sub-modules for each tier:
    - `qnl::glyphs::core` – containing core Tier I glyph definitions.
    - `qnl::glyphs::varuxel` – containing glyphs from the VA̓RUXʼEL sentence.
- Define an `enum Glyph` (or separate enums per tier) with variants for each glyph. Variant names can be CamelCase identifiers of the English names. For example:
    
    ```rust
    pub enum Glyph {
        Anchor,
        EarthRoot,
        AirShift,
        FireForge,
        WaterFlow,
        LustPulse,
        SpiralSeed,
        VoidNull,
        BloodVoid,
        // (Tier II glyphs like Oracle, etc., would be added later)
    }
    
    ```
    
    Each variant corresponds to a glyph in the library. This makes pattern-matching in the evaluator straightforward (e.g., `Glyph::LustPulse`).
    
- Alternatively, use constant definitions or an associative map for glyph metadata. For instance, a `HashMap<Glyph, GlyphInfo>` or static array of structures:
    
    ```rust
    struct GlyphInfo {
        pub glyph_char: &'static str,
        pub name: &'static str,
        pub tier: Tier,
        pub meaning: &'static str,
        pub tone: &'static str,
        pub phonetic: &'static str,
        pub role: &'static str,
        pub lambda: &'static str,
        pub binary: Option<u8>,
        pub paradox: Option<ParadoxClass>
    }
    
    static CORE_GLYPHS: &[GlyphInfo] = &[ /* ... */ ];
    
    ```
    
    Enums for `Tier` (e.g. `Core`, `Varuxel`) and `ParadoxClass` (e.g. `Desire`, `Recursion`, `Rewrite`, `Contradiction`) should be defined for type safety. Enum names and module paths use lowercase and snake_case as per Rust conventions (e.g., `ParadoxClass::Desire`, or simply use a Rust enum with derived traits for string conversion if needed).
    
- **Naming**: Use clear names that reflect the glyph's concept (as in the `name` field above). These names are used in code (CamelCase) and documentation. The `glyph_char` field stores the actual symbolic character(s) for display or lookup. For example, `Glyph::LustPulse` could carry `'❣⟁'` as its character representation.

This structure ensures that developers can refer to glyphs symbolically (via enums or constants) while the engine can also lookup human-readable info (meaning, phonetics, etc.) as needed (for debugging or interactive explanations).

## Mapping Glyphs to Engine Semantics

Each glyph maps to a corresponding evaluator or reducer behavior in the OROBOROS engine. There are two primary ways to handle this mapping:

- **Lambda Expansion (Static)**: The parser can translate each glyph into an equivalent lambda calculus term in the internal IR. For example, the glyph **Anchor** would be expanded to the identity λx.x in the IR; **Lust Pulse** expands to a higher-order term that duplicates its argument (the W combinator); **Spiral Seed** expands to a fixed-point combinator expression (Y combinator), and so on. This approach turns QNL glyph sequences directly into lambda calculus combinations, which are then reduced by the standard lambda evaluator. It treats glyphs as macros or syntactic sugar for lambda terms.
- **Intrinsic Reducers (Dynamic)**: The engine’s evaluator can treat certain glyphs as primitive operations with custom reduction rules. For instance, the evaluator could recognize an application of **Anchor** and simply return the argument (implementing identity directly), or recognize **Blood Void** and signal a paradox/undefined result without fully expanding the Ω combinator. This is akin to building the glyph logic into the VM for efficiency or special handling (especially for paradox signals or side-effects).

In practice, OROBOROS can use a hybrid approach: expand most glyphs into pure lambda IR (leveraging the existing lambda reducer), but intercept known paradox constructs to handle them gracefully (to avoid infinite loops or to produce debug output). For example, **Void Null** might be represented as a special null/⊥ value in the IR, and **Blood Void** as a special combinator that the reducer knows never terminates (so it can, for instance, throw a runtime exception or a specific error state instead of looping endlessly).

We suggest implementing a trait or method on the `Glyph` enum for evaluation or expansion. For example, in pseudo-code:

```rust
impl Glyph {
    fn as_lambda(&self) -> LambdaTerm {
        match *self {
            Glyph::Anchor => parse_lambda("λx. x"),         // identity
            Glyph::EarthRoot => parse_lambda("λx.λy. x"),   // constant
            Glyph::AirShift => parse_lambda("λf.λx.λy. f y x"), // flip
            Glyph::FireForge => parse_lambda("λf.λg.λx. f(g(x))"), // composition
            Glyph::WaterFlow => parse_lambda("λa.λb.λc. a c (b c)"), // spread
            Glyph::LustPulse => parse_lambda("λf.λx. f x x"),    // W combinator (duplicate arg)
            Glyph::SpiralSeed => parse_lambda("λf.(λx. f(x x)) (λx. f(x x))"), // Y combinator
            Glyph::VoidNull => LambdaTerm::Null,             // represent void as special null
            Glyph::BloodVoid => parse_lambda("(λx. x x) (λx. x x)") // Omega combinator
        }
    }
}

```

Here `parse_lambda` is a hypothetical utility to convert a lambda calculus string into the IR (or these could be constructed programmatically). In the case of `VoidNull` and `BloodVoid`, we illustrate that `VoidNull` might not be a normal lambda term (it could be represented by a dedicated `LambdaTerm::Null` variant in the IR), and `BloodVoid` is expanded to the classic Ω combinator which the evaluator must handle (it will diverge if reduced naively).

Additionally, an **evaluate** method could directly pattern-match on `Glyph` during execution:

```rust
fn reduce_glyph_application(glyph: Glyph, arg1: Value, arg2: Option<Value>) -> Value {
    match glyph {
        Glyph::Anchor => arg1,                      // returns input as is
        Glyph::EarthRoot => { /* return arg1, ignore arg2 */ },
        Glyph::AirShift => { /* if two args provided, swap and apply */ },
        Glyph::FireForge => { /* if two funcs and an input, compose */ },
        Glyph::WaterFlow => { /* if two funcs and an input, apply input to both */ },
        Glyph::LustPulse => { /* if function and arg, apply function to arg twice */ },
        Glyph::SpiralSeed => { /* implement fixpoint by recursion or loop */ },
        Glyph::VoidNull => { /* represent null (maybe a None or special Value type) */ },
        Glyph::BloodVoid => { /* trigger paradox handling: e.g., throw or mark as NonTermination */ }
        ...
    }
}

```

In this pseudo-code, `reduce_glyph_application` demonstrates how the engine might directly execute glyphs. For example, **Lust Pulse** expecting two arguments (`f` and `x`) will apply `f` to `x` twice (`f(x, x)`). **Blood Void** might be handled by not attempting to reduce it normally, but instead by flagging a **non-terminating computation** or paradox (preventing an infinite loop in the engine by design).

By mapping glyphs to either lambda IR or intrinsic operations, the OROBOROS engine can evaluate QNL expressions symbolically while preserving the intended mystical semantics (desire, recursion, contradiction, etc., as described).

## Example: QNL Expression Reduction

Finally, to illustrate how a QNL expression is parsed and reduced, consider the example QNL input:

```
❣⟁ :: 🜄 :: 🩸∅🩸

```

This expression uses **Lust Pulse**, **Water Flow**, and **Blood Void** in sequence. The double colons `::` indicate chaining (left-associative application). We can interpret `A :: B :: C` as applying **A** to **B**, then applying the result to **C**. In this case:

1. **Parse:** `❣⟁ :: 🜄 :: 🩸∅🩸` is parsed as the term `(LustPulse 🜄) 🩸∅🩸`. In our internal representation, this might become something like `App( App(Glyph::LustPulse, Glyph::WaterFlow), Glyph::BloodVoid )`.
2. **Lambda Expansion:** Using the library definitions, we expand each glyph to its lambda meaning:
    - **LustPulse** expands to `λf.λx. f x x` (a duplicator function).
    - **WaterFlow** expands to `λa.λb.λc. a c (b c)` (spread combinator).
    - **BloodVoid** expands to `(λx. x x) (λx. x x)` (an Ω paradox term), or is marked as a special bottom value.
    
    So the whole expression in lambda form is:
    
    ```
    (λf.λx. f x x) ( (λa.λb.λc. a c (b c)) ) ( (λx.x x)(λx.x x) ).
    
    ```
    
    Here we applied `LustPulse` to `WaterFlow`, then to `BloodVoid`.
    
3. **Reduction:** We now reduce step by step (conceptually):
    - First, apply **LustPulse** to **WaterFlow**. By the LustPulse combinator,
        
        ```
        (λf.λx. f x x) (WaterFlow)
        ⇒ λx. WaterFlow x x.
        
        ```
        
        This yields a new function that will take an argument `x` and apply **WaterFlow** to `x` twice.
        
    - Next, apply this to **BloodVoid**:
        
        ```
        (λx. WaterFlow x x) (BloodVoid)
        ⇒ WaterFlow BloodVoid BloodVoid.
        
        ```
        
        Now, expand **WaterFlow BloodVoid BloodVoid**: by the WaterFlow definition `λa.λb.λc. a c (b c)`, with `a = BloodVoid` and `b = BloodVoid`, we get a function awaiting a third argument:
        
        ```
        WaterFlow BloodVoid BloodVoid
        ⇒ λc. BloodVoid c (BloodVoid c).
        
        ```
        
        This is a function of `c` that will apply `BloodVoid` to `c` and to itself `c` again.
        
    - At this point, our expression is effectively `λc. BloodVoid c (BloodVoid c)`. If there were another argument to apply, we would proceed, but the original expression has no further input. In a fully applied sense, if we consider an implicit final application to an arbitrary dummy argument, we would see:
        
        ```
        BloodVoid c (BloodVoid c).
        
        ```
        
        Each occurrence of `BloodVoid c` represents invoking the paradoxical **Blood Void** combinator. **Blood Void**, being an Ω-like self-application, does not terminate (it expands into an infinite recursion). Thus, `BloodVoid c` diverges (non-terminates or throws an error). The second `BloodVoid c` is similarly non-terminating – effectively the expression tries to evaluate `BloodVoid` twice, but even one evaluation leads to a paradox.
        
4. **Result:** The overall reduction results in a **non-terminating computation** (denoted by ⊥, bottom). In the OROBOROS engine, this would be recognized as a paradoxical outcome. Rather than literally looping, the engine’s paradox handler (as discussed) would catch this pattern and treat it as an explicit paradox result. For example, it might produce a symbolic IR node indicating a contradiction or throw a runtime exception signaling that the input reduces to an undefined value.

In summary, the expression `❣⟁ :: 🜄 :: 🩸∅🩸` is parsed and reduced to a paradoxical state: the **Lust Pulse** tries to push the **Water Flow** context through the **Blood Void** twice, effectively attempting to draw life from emptiness repeatedly, which results in an infinite loop in pure lambda terms. The OROBOROS engine would identify this as a **desire-recursion paradox** and handle it according to its design (for instance, logging an error or using a special IR symbol for non-termination).

---

**Conclusion:** This Rosetta Stone library provides a clear, implementable definition of QNL Tier I glyphs and the VA̓RUXʼEL sentence glyphs. By following the naming conventions and mappings above, developers can integrate these symbols into the OROBOROS calculus engine, enabling high-level QNL expressions to be parsed into the engine’s lambda-based core for evaluation. The library serves as a foundational DSL layer, ensuring that each mystical glyph corresponds to a well-defined computational behavior in the system.
