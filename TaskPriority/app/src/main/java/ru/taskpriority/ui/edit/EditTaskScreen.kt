package ru.taskpriority.ui.edit

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringArrayResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlin.math.roundToInt
import ru.taskpriority.R
import ru.taskpriority.domain.ZoneThresholds
import ru.taskpriority.ui.AppViewModelProvider
import ru.taskpriority.ui.components.MILLIS_PER_DAY
import ru.taskpriority.ui.components.formatEpochDay
import ru.taskpriority.ui.theme.colors

/** Экран создания и редактирования задачи. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditTaskScreen(
    onDone: () -> Unit,
    viewModel: EditTaskViewModel = viewModel(factory = AppViewModelProvider.Factory),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    // Как только ViewModel сообщила «сохранено» — закрываем экран.
    LaunchedEffect(state.isSaved) {
        if (state.isSaved) onDone()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        stringResource(if (state.isNew) R.string.edit_title_new else R.string.edit_title_existing),
                        fontWeight = FontWeight.Bold,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onDone) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.action_back))
                    }
                },
                actions = {
                    IconButton(onClick = viewModel::save) {
                        Icon(Icons.Filled.Check, contentDescription = stringResource(R.string.action_save))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
    ) { innerPadding ->
        if (state.isLoading) {
            Box(Modifier.padding(innerPadding).fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            return@Scaffold
        }

        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .imePadding() // поля не прячутся под клавиатурой
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // ---- Название (обязательно) ----
            OutlinedTextField(
                value = state.title,
                onValueChange = viewModel::onTitleChange,
                label = { Text(stringResource(R.string.field_title)) },
                isError = state.showTitleError,
                supportingText = {
                    if (state.showTitleError) Text(stringResource(R.string.error_title_required))
                },
                singleLine = true,
                keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences),
                modifier = Modifier.fillMaxWidth(),
            )

            // ---- Описание (необязательно) ----
            OutlinedTextField(
                value = state.description,
                onValueChange = viewModel::onDescriptionChange,
                label = { Text(stringResource(R.string.field_description)) },
                minLines = 3,
                keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences),
                modifier = Modifier.fillMaxWidth(),
            )

            // ---- Слайдеры значимости и сложности ----
            LevelSlider(
                label = stringResource(R.string.field_importance),
                value = state.importance,
                levelNames = stringArrayResource(R.array.importance_levels).toList(),
                onValueChange = viewModel::onImportanceChange,
            )
            LevelSlider(
                label = stringResource(R.string.field_difficulty),
                value = state.difficulty,
                levelNames = stringArrayResource(R.array.difficulty_levels).toList(),
                onValueChange = viewModel::onDifficultyChange,
            )

            // ---- Подсказка: в какую зону попадёт задача ----
            ZonePreview(state)

            // ---- Срок выполнения ----
            DueDateField(
                dueDateEpochDay = state.dueDateEpochDay,
                onDueDateChange = viewModel::onDueDateChange,
            )

            // ---- Статус (только для существующей задачи) ----
            if (!state.isNew) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = state.isDone, onCheckedChange = viewModel::onDoneChange)
                    Text(stringResource(R.string.field_done))
                }
            }

            Button(
                onClick = viewModel::save,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(stringResource(R.string.action_save))
            }
        }
    }
}

/**
 * Слайдер с шагом 1 и подписями.
 * steps = количество промежуточных делений между краями: для шкалы 1..5 это 3 (2, 3, 4).
 */
@Composable
private fun LevelSlider(
    label: String,
    value: Int,
    levelNames: List<String>,
    onValueChange: (Int) -> Unit,
) {
    val min = ZoneThresholds.SCALE_MIN
    val max = ZoneThresholds.SCALE_MAX
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(label, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Text(
                text = "$value — ${levelNames.getOrElse(value - min) { "" }}",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )
        }
        Slider(
            value = value.toFloat(),
            onValueChange = { onValueChange(it.roundToInt()) },
            valueRange = min.toFloat()..max.toFloat(),
            steps = max - min - 1,
            colors = SliderDefaults.colors(
                thumbColor = MaterialTheme.colorScheme.primary,
                activeTrackColor = MaterialTheme.colorScheme.primary,
            ),
        )
        // Цифры под делениями
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            for (level in min..max) {
                Text(
                    text = level.toString(),
                    style = MaterialTheme.typography.labelSmall,
                    color = if (level == value) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = if (level == value) FontWeight.Bold else FontWeight.Normal,
                    modifier = Modifier.padding(horizontal = 6.dp),
                )
            }
        }
        // Подписи крайних значений
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(levelNames.first(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(levelNames.last(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Плашка «Попадёт в зону …», окрашенная в цвет зоны. */
@Composable
private fun ZonePreview(state: EditTaskUiState) {
    val zone = state.zone
    val colors = zone.colors()
    Surface(
        color = colors.container,
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier
                    .size(16.dp)
                    .background(colors.accent, CircleShape)
            )
            Spacer(Modifier.width(12.dp))
            Column {
                Text(
                    text = stringResource(R.string.edit_zone_preview, stringResource(zone.titleRes)),
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = stringResource(zone.hintRes),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

/** Кнопка выбора срока + крестик для очистки + диалог календаря. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DueDateField(
    dueDateEpochDay: Long?,
    onDueDateChange: (Long?) -> Unit,
) {
    var showPicker by rememberSaveable { mutableStateOf(false) }

    Column {
        Text(stringResource(R.string.field_due_date), style = MaterialTheme.typography.titleMedium)
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(onClick = { showPicker = true }, modifier = Modifier.weight(1f)) {
                Icon(Icons.Filled.DateRange, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(
                    dueDateEpochDay?.let { formatEpochDay(it) } ?: stringResource(R.string.due_date_none)
                )
            }
            if (dueDateEpochDay != null) {
                IconButton(onClick = { onDueDateChange(null) }) {
                    Icon(Icons.Filled.Close, contentDescription = stringResource(R.string.due_date_clear))
                }
            }
        }
    }

    if (showPicker) {
        // DatePicker работает с миллисекундами UTC (полночь выбранного дня),
        // а мы храним номер дня — переводим туда и обратно через MILLIS_PER_DAY.
        val pickerState = rememberDatePickerState(
            initialSelectedDateMillis = dueDateEpochDay?.let { it * MILLIS_PER_DAY },
        )
        DatePickerDialog(
            onDismissRequest = { showPicker = false },
            confirmButton = {
                TextButton(onClick = {
                    pickerState.selectedDateMillis?.let { onDueDateChange(it / MILLIS_PER_DAY) }
                    showPicker = false
                }) { Text(stringResource(R.string.action_choose)) }
            },
            dismissButton = {
                TextButton(onClick = { showPicker = false }) { Text(stringResource(R.string.action_cancel)) }
            },
        ) {
            DatePicker(state = pickerState)
        }
    }
}
