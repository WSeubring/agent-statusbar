/**
 * Pi status footer for agent-statusbar.
 *
 * Native pi data:
 * - model
 * - thinking level via pi.getThinkingLevel()
 * - context usage via ctx.getContextUsage()
 * - git branch via footerData.getGitBranch()
 * - cumulative token and cost stats via session history
 *
 * Optional quota inputs:
 * - PI_STATUS_SESSION_PCT / PI_STATUS_WEEKLY_PCT
 * - or PI_STATUS_LIMITS_FILE with: { "session": 54, "weekly": 81 }
 */

import type { AssistantMessage } from "@mariozechner/pi-ai";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@mariozechner/pi-tui";
import fs from "node:fs";
import path from "node:path";

function parsePercent(value: unknown): number | undefined {
	if (value === null || value === undefined || value === "") return undefined;
	if (typeof value === "number" && Number.isFinite(value)) {
		if (value >= 0 && value <= 1) return value * 100;
		if (value >= 0 && value <= 100) return value;
		return undefined;
	}
	if (typeof value === "string") {
		const match = value.match(/(-?\d+(?:\.\d+)?)\s*%?/);
		if (!match) return undefined;
		const num = Number(match[1]);
		if (!Number.isFinite(num)) return undefined;
		if (num >= 0 && num <= 1 && !value.includes("%")) return num * 100;
		if (num >= 0 && num <= 100) return num;
	}
	return undefined;
}

function clampPct(value: number | undefined): number | undefined {
	if (value === undefined) return undefined;
	return Math.max(0, Math.min(100, value));
}

function formatPct(value: number | undefined): string {
	return value === undefined ? "--" : `${Math.round(value)}%`;
}

function miniBar(value: number | undefined, width = 8): string {
	if (value === undefined) return "░".repeat(width);
	const filled = Math.max(0, Math.min(width, Math.round((value / 100) * width)));
	return "█".repeat(filled) + "░".repeat(width - filled);
}

function fmtTokens(n: number): string {
	if (n < 1000) return `${n}`;
	if (n < 1_000_000) return `${(n / 1000).toFixed(1)}k`;
	return `${(n / 1_000_000).toFixed(1)}m`;
}

function formatModelLabel(model: any, thinkingLevel: string | undefined): string | undefined {
	const base = model?.name || model?.id;
	if (!base) return undefined;
	if (!model?.reasoning) return base;
	return `${base} (${thinkingLevel || "off"})`;
}

function icon(name: "ctx" | "branch"): string {
	const ascii = process.env.PI_STATUS_ASCII === "1";
	if (ascii) {
		switch (name) {
			case "ctx":
				return "ctx";
			case "branch":
				return "git";
		}
	}

	switch (name) {
		case "ctx":
			return "◔";
		case "branch":
			return "";
	}
}

function readLimitData(): { session?: number; weekly?: number } {
	const fromFile = process.env.PI_STATUS_LIMITS_FILE;
	if (fromFile && fs.existsSync(fromFile)) {
		try {
			const json = JSON.parse(fs.readFileSync(fromFile, "utf8"));
			return {
				session: clampPct(parsePercent(json.session ?? json.sessionPct ?? json.session_percent)),
				weekly: clampPct(parsePercent(json.weekly ?? json.weeklyPct ?? json.weekly_percent)),
			};
		} catch {
			// ignore invalid file and fall back to env vars
		}
	}

	return {
		session: clampPct(parsePercent(process.env.PI_STATUS_SESSION_PCT)),
		weekly: clampPct(parsePercent(process.env.PI_STATUS_WEEKLY_PCT)),
	};
}

function installFooter(pi: ExtensionAPI, ctx: any) {
	ctx.ui.setFooter((tui: any, theme: any, footerData: any) => {
		const unsubscribe = footerData.onBranchChange(() => tui.requestRender());

		return {
			dispose: unsubscribe,
			invalidate() {},
			render(width: number): string[] {
				const usage = ctx.getContextUsage();
				const contextPct = clampPct(parsePercent(usage?.percent));
				const contextTokens = usage?.tokens ?? undefined;
				const limits = readLimitData();

				let input = 0;
				let output = 0;
				let cost = 0;
				for (const entry of ctx.sessionManager.getBranch()) {
					if (entry.type !== "message" || entry.message.role !== "assistant") continue;
					const message = entry.message as AssistantMessage;
					input += message.usage.input || 0;
					output += message.usage.output || 0;
					cost += message.usage.cost.total || 0;
				}

				const soft = (text: string) => theme.fg("dim", text);
				const muted = (text: string) => theme.fg("muted", text);
				const good = (text: string) => theme.fg("success", text);
				const warn = (text: string) => theme.fg("warning", text);
				const bad = (text: string) => theme.fg("error", text);
				const accent = (text: string) => theme.fg("accent", text);
				const divider = soft(" │ ");

				const paint = (
					tone: "accent" | "muted" | "dim" | "success" | "warning" | "error",
					text: string,
				) => {
					if (tone === "accent") return accent(text);
					if (tone === "muted") return muted(text);
					if (tone === "dim") return soft(text);
					if (tone === "success") return good(text);
					if (tone === "warning") return warn(text);
					return bad(text);
				};

				const labelValue = (
					label: string,
					value: string | undefined,
					labelTone: "accent" | "muted" | "dim" | "success" | "warning" | "error" = "muted",
					valueTone: "accent" | "muted" | "dim" | "success" | "warning" | "error" = "dim",
				) => {
					if (!value) return paint(labelTone, label);
					return `${paint(labelTone, label)} ${paint(valueTone, value)}`;
				};

				const valueOnly = (
					value: string,
					tone: "accent" | "muted" | "dim" | "success" | "warning" | "error" = "muted",
				) => paint(tone, value);

				const contextTone = contextPct !== undefined && contextPct >= 90
					? "error"
					: contextPct !== undefined && contextPct >= 70
						? "warning"
						: "muted";

				let contextValue = `${icon("ctx")} ${miniBar(contextPct)} ${formatPct(contextPct)}`;
				if (contextTokens) contextValue += ` ${fmtTokens(contextTokens)}`;

				const quotaSegment = (name: "session" | "weekly", value: number | undefined, threshold: number) => {
					if (value === undefined) return undefined;
					const tone = value >= 90 ? "error" : value >= threshold ? "warning" : "muted";
					return labelValue(name, formatPct(value), tone);
				};

				const leftParts: string[] = [labelValue("PI", undefined, "accent")];

				const modelLabel = formatModelLabel(ctx.model, pi.getThinkingLevel());
				if (modelLabel) {
					leftParts.push(valueOnly(modelLabel, "muted"));
				}

				leftParts.push(`${muted("ctx")} ${paint(contextTone, contextValue)}`);

				const sessionSegment = quotaSegment("session", limits.session, 50);
				if (sessionSegment) leftParts.push(sessionSegment);

				const weeklySegment = quotaSegment("weekly", limits.weekly, 75);
				if (weeklySegment) leftParts.push(weeklySegment);

				const branch = footerData.getGitBranch();
				const cwdName = path.basename(ctx.cwd || process.cwd()) || ctx.cwd || ".";
				const locationLine = muted(branch ? `${cwdName} (${branch})` : cwdName);
				const rightParts = [
					soft(`in ${fmtTokens(input)}`),
					soft(`out ${fmtTokens(output)}`),
					soft(`$${cost.toFixed(3)}`),
				].filter(Boolean);

				const left = leftParts.join(divider);
				const right = rightParts.join(divider);

				if (!right) return [truncateToWidth(left, width), truncateToWidth(locationLine, width)];

				const space = width - visibleWidth(left) - visibleWidth(right);
				if (space >= 2) {
					return [
						truncateToWidth(left + " ".repeat(space) + right, width),
						truncateToWidth(locationLine, width),
					];
				}

				return [truncateToWidth(left, width), truncateToWidth(right, width), truncateToWidth(locationLine, width)];
			},
		};
	});
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", async (_event, ctx) => installFooter(pi, ctx));
	pi.on("model_select", async (_event, ctx) => installFooter(pi, ctx));
	pi.on("turn_end", async (_event, ctx) => installFooter(pi, ctx));
}
