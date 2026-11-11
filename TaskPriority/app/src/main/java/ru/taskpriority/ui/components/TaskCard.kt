package ru.taskpriority.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import ru.taskpriority.R
import ru.taskpriority.data.Task
import ru.taskpriority.domain.zone
import ru.taskpriority.ui.theme.colors

/**
 * Карточка задачи.
 *
 * @param compact компактный вид для узких ячеек матрицы (без описания, короткие подписи).
 * @param showZone показывать ли название зоны (полезно в общем списке).
 */
@Composable
fun TaskCard(
    task: Task,
    onClick: () -> Unit,
    onToggleDone: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
    compact: Boolean = false,
    showZone: Boolean = false,
) {
    val zoneColors = task.zone.colors()
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLowest),
    ) {
        // IntrinsicSize.Min позволяет цветной полоске слева растянуться на всю высоту карточки.
        Row(
            modifier = Modifier
                .height(IntrinsicSize.Min)
                .alpha(if (task.isDone) 0.6f else 1f),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                Modifier
                    .width(if (compact) 4.dp else 6.dp)
                    .fillMaxHeight()
                    .background(zoneColors.accent)
            )
            Checkbox(
                checked = task.isDone,
                onCheckedChange = onToggleDone,
                colors = CheckboxDefaults.colors(checkedColor = zoneColors.accent),
            )
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(top = 8.dp, bottom = 8.dp, end = 10.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text(
                    text = task.title,
                    style = if (compact) MaterialTheme.typography.bodyMedium else MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    textDecoration = if (task.isDone) TextDecoration.LineThrough else null,
                )
                if (!compact && task.description.isNotBlank()) {
                    Text(
                        text = task.description,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
                TaskInfoRow(task = task, compact = compact, showZone = showZone, zoneAccent = zoneColors.accent)
            }
        }
    }
}

/** Строка с «пилюлями»: значимость, сложность, срок и (опционально) зона. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun TaskInfoRow(task: Task, compact: Boolean, showZone: Boolean, zoneAccent: Color) {
    val overdue = isOverdue(task.dueDateEpochDay, task.isDone)
    FlowRow(
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        if (compact) {
            InfoPill(stringResource(R.string.card_short_levels, task.importance, task.difficulty))
        } else {
            InfoPill(stringResource(R.string.card_importance, task.importance))
            InfoPill(stringResource(R.string.card_difficulty, task.difficulty))
        }
        task.dueDateEpochDay?.let { day ->
            InfoPill(
                text = if (overdue) stringResource(R.string.card_overdue, formatEpochDay(day))
                else stringResource(R.string.card_due, formatEpochDay(day)),
                highlighted = overdue,
            )
        }
        if (showZone) {
            InfoPill(stringResource(task.zone.titleRes), accent = zoneAccent)
        }
    }
}

/** Маленькая скруглённая подпись. */
@Composable
private fun InfoPill(text: String, highlighted: Boolean = false, accent: Color? = null) {
    val container = when {
        highlighted -> MaterialTheme.colorScheme.error
        accent != null -> accent
        else -> MaterialTheme.colorScheme.secondaryContainer
    }
    val content = when {
        highlighted -> MaterialTheme.colorScheme.onError
        accent != null -> Color.White
        else -> MaterialTheme.colorScheme.onSecondaryContainer
    }
    Surface(color = container, contentColor = content, shape = RoundedCornerShape(50)) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
            maxLines = 1,
        )
    }
}
