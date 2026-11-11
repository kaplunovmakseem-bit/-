package ru.taskpriority.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import ru.taskpriority.domain.PriorityZone
import ru.taskpriority.ui.theme.colors

/** Цветная шапка зоны: название, подсказка и счётчик активных задач. */
@Composable
fun ZoneHeader(zone: PriorityZone, count: Int, modifier: Modifier = Modifier) {
    val colors = zone.colors()
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(colors.accent)
            .padding(horizontal = 10.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                text = stringResource(zone.titleRes),
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold,
                color = colors.onAccent,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = stringResource(zone.hintRes),
                style = MaterialTheme.typography.labelSmall,
                color = colors.onAccent.copy(alpha = 0.85f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        // Счётчик задач в кружке
        Box(
            modifier = Modifier
                .sizeIn(minWidth = 28.dp, minHeight = 28.dp)
                .background(colors.onAccent, CircleShape)
                .padding(horizontal = 6.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                color = colors.accent,
            )
        }
    }
}
