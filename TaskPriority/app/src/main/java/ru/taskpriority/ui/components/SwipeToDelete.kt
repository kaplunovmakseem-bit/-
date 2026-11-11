package ru.taskpriority.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import ru.taskpriority.R

/**
 * Обёртка, позволяющая удалить элемент свайпом влево или вправо.
 * ВАЖНО: в LazyColumn элементы должны иметь key (id задачи), иначе состояние свайпа
 * «переедет» на соседний элемент после удаления.
 */
@Composable
fun SwipeToDeleteBox(
    onDelete: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val state = rememberSwipeToDismissBoxState()
    val currentOnDelete by rememberUpdatedState(onDelete)

    // Как только карточка «улетела» за край экрана — удаляем задачу.
    LaunchedEffect(state.currentValue) {
        if (state.currentValue != SwipeToDismissBoxValue.Settled) currentOnDelete()
    }

    SwipeToDismissBox(
        state = state,
        modifier = modifier,
        backgroundContent = {
            // Красный фон с корзиной, который виден под карточкой во время свайпа.
            val alignment = if (state.dismissDirection == SwipeToDismissBoxValue.EndToStart) {
                Alignment.CenterEnd
            } else {
                Alignment.CenterStart
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.error)
                    .padding(horizontal = 16.dp),
                contentAlignment = alignment,
            ) {
                Icon(
                    imageVector = Icons.Filled.Delete,
                    contentDescription = stringResource(R.string.action_delete),
                    tint = MaterialTheme.colorScheme.onError,
                )
            }
        },
    ) {
        content()
    }
}

/**
 * Показывает Snackbar с кнопкой «Отменить». Если пользователь нажал её — вызывается [onUndo].
 * Предыдущий Snackbar закрывается, чтобы сообщения не копились в очереди.
 */
fun CoroutineScope.showUndoSnackbar(
    snackbarHostState: SnackbarHostState,
    message: String,
    actionLabel: String,
    onUndo: () -> Unit,
) {
    launch {
        snackbarHostState.currentSnackbarData?.dismiss()
        val result = snackbarHostState.showSnackbar(
            message = message,
            actionLabel = actionLabel,
            duration = SnackbarDuration.Short,
        )
        if (result == SnackbarResult.ActionPerformed) onUndo()
    }
}
