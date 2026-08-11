from __future__ import annotations

from dataclasses import dataclass

from poker_training_bot.strategy.contract import (
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)


@dataclass(frozen=True)
class CheckFoldStrategy:
    """Contract reference strategy, not a playing strategy.

    Always takes the passive action: check when free, fold when facing a bet,
    and refuse (fail closed) when neither is legal.
    """

    strategy_id: str = "reference-check-fold"
    strategy_version: int = 1

    def decide(self, query: StrategyQuery) -> StrategyDecision | StrategyRefusal:
        if "check" in query.legal_actions:
            return StrategyDecision("check", None, "reference:check-when-free")
        if "fold" in query.legal_actions:
            return StrategyDecision("fold", None, "reference:fold-facing-bet")
        return StrategyRefusal("reference:no-passive-action")
