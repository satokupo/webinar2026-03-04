const vscode = require('vscode');

async function findTerminalByPid(pid) {
    const terminals = vscode.window.terminals;
    const results = await Promise.all(
        terminals.map(async (t) => ({ terminal: t, pid: await t.processId }))
    );
    const match = results.find((r) => r.pid === pid);
    return match ? match.terminal : undefined;
}

async function renameTerminal(pid, name) {
    let target;
    if (pid !== undefined) {
        target = await findTerminalByPid(pid);
        if (!target) {
            vscode.window.showWarningMessage(
                `Tab Renamer: PID ${pid} のターミナルが見つかりません`
            );
            return;
        }
    } else {
        target = vscode.window.activeTerminal;
        if (!target) {
            vscode.window.showWarningMessage(
                'Tab Renamer: アクティブなターミナルがありません'
            );
            return;
        }
    }

    // 現在のアクティブターミナルを記憶
    const previous = vscode.window.activeTerminal;

    // 対象ターミナルをフォーカス（renameWithArg はアクティブターミナルに作用する）
    target.show(false);
    await new Promise((resolve) => setTimeout(resolve, 150));

    // リネーム実行
    await vscode.commands.executeCommand(
        'workbench.action.terminal.renameWithArg',
        { name }
    );

    // 元のターミナルにフォーカスを戻す
    if (previous && previous !== target) {
        previous.show(false);
    }
}

class TabRenamerUriHandler {
    handleUri(uri) {
        const params = new URLSearchParams(uri.query);
        const pidStr = params.get('pid');
        const name = params.get('name');

        if (!name) {
            vscode.window.showWarningMessage(
                'Tab Renamer: "name" パラメータが必要です'
            );
            return;
        }

        const pid = pidStr ? parseInt(pidStr, 10) : undefined;
        if (pidStr && isNaN(pid)) {
            vscode.window.showWarningMessage(
                `Tab Renamer: 無効な PID "${pidStr}"`
            );
            return;
        }

        renameTerminal(pid, name);
    }
}

function activate(context) {
    context.subscriptions.push(
        vscode.window.registerUriHandler(new TabRenamerUriHandler())
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('tab-renamer.rename', async (args) => {
            if (!args || !args.name) {
                vscode.window.showWarningMessage(
                    'Tab Renamer: "name" 引数が必要です'
                );
                return;
            }
            await renameTerminal(args.pid, args.name);
        })
    );
}

function deactivate() {}

module.exports = { activate, deactivate };
