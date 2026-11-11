package ru.taskpriority.ui.components

import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.res.stringResource
import ru.taskpriority.R
import ru.taskpriority.data.Task
import ru.taskpriority.ui.TaskActionsViewModel

/**
 * Готовые обработчики «удалить» и «отметить выполненной» со Snackbar-отменой.
 * Используются на всех экранах со списками задач, чтобы поведение было одинаковым.
 */
class TaskActionHandlers(
    val onDelete: (Task) -> Unit,
    val onToggleDone: (Task, Boolean) -> Unit,
)

@Composable
fun rememberTaskActionHandlers(
    viewModel: TaskActionsViewModel,
    snackbarHostState: SnackbarHostState,
): TaskActionHandlers {
    val scope = rememberCoroutineScope()
    val deletedMsg = stringResource(R.string.snackbar_deleted)
    val doneMsg = stringResource(R.string.snackbar_done)
    val undo = stringResource(R.string.action_undo)

    return remember(viewModel, snackbarHostState, deletedMsg, doneMsg, undo) {
        TaskActionHandlers(
            onDelete = { task ->
                viewModel.delete(task)
                scope.showUndoSnackbar(snackbarHostState, deletedMsg, undo) { viewModel.restore(task) }
            },
            onToggleDone = { task, done ->
                viewModel.setDone(task, done)
                // Отмену предлагаем только когда задачу отметили выполненной —
                // на матрице она в этот момент исчезает из ячейки.
                if (done) {
                    scope.showUndoSnackbar(snackbarHostState, doneMsg, undo) { viewModel.setDone(task, false) }
                }
            },
        )
    }
}
