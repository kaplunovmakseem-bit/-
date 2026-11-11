package ru.taskpriority.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import ru.taskpriority.domain.PriorityZone

private val LightColors = lightColorScheme(
    primary = RedPrimaryLight,
    onPrimary = RedOnPrimaryLight,
    primaryContainer = RedPrimaryContainerLight,
    onPrimaryContainer = RedOnPrimaryContainerLight,
    secondary = RedSecondaryLight,
    secondaryContainer = RedSecondaryContainerLight,
    onSecondaryContainer = RedOnSecondaryContainerLight,
    tertiary = RedTertiaryLight,
    background = RedBackgroundLight,
    onBackground = RedOnBackgroundLight,
    surface = RedBackgroundLight,
    onSurface = RedOnBackgroundLight,
    surfaceVariant = RedSurfaceVariantLight,
    onSurfaceVariant = RedOnSurfaceVariantLight,
    outline = RedOutlineLight,
    surfaceContainerLowest = RedSurfaceContainerLowestLight,
    surfaceContainerLow = RedSurfaceContainerLowLight,
    surfaceContainer = RedSurfaceContainerLight,
    surfaceContainerHigh = RedSurfaceContainerHighLight,
    surfaceContainerHighest = RedSurfaceContainerHighestLight,
)

private val DarkColors = darkColorScheme(
    primary = RedPrimaryDark,
    onPrimary = RedOnPrimaryDark,
    primaryContainer = RedPrimaryContainerDark,
    onPrimaryContainer = RedOnPrimaryContainerDark,
    secondary = RedSecondaryDark,
    secondaryContainer = RedSecondaryContainerDark,
    onSecondaryContainer = RedOnSecondaryContainerDark,
    tertiary = RedTertiaryDark,
    background = RedBackgroundDark,
    onBackground = RedOnBackgroundDark,
    surface = RedBackgroundDark,
    onSurface = RedOnBackgroundDark,
    surfaceVariant = RedSurfaceVariantDark,
    onSurfaceVariant = RedOnSurfaceVariantDark,
    outline = RedOutlineDark,
    surfaceContainerLowest = RedSurfaceContainerLowestDark,
    surfaceContainerLow = RedSurfaceContainerLowDark,
    surfaceContainer = RedSurfaceContainerDark,
    surfaceContainerHigh = RedSurfaceContainerHighDark,
    surfaceContainerHighest = RedSurfaceContainerHighestDark,
)

/**
 * Тема приложения. Светлая/тёмная выбирается по настройке системы.
 * Динамические цвета Android 12+ (Material You) намеренно НЕ используем,
 * чтобы приложение всегда оставалось красным.
 */
@Composable
fun TaskPriorityTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = AppTypography,
        content = content,
    )
}

/** Цвета одной зоны матрицы. */
data class ZoneColors(
    val accent: Color,
    val onAccent: Color,
    val container: Color,
)

/** Возвращает цвета зоны с учётом текущей темы (светлая/тёмная). */
@Composable
fun PriorityZone.colors(): ZoneColors {
    val dark = isSystemInDarkTheme()
    return when (this) {
        PriorityZone.DO_NOW -> if (dark) ZoneColors(ZoneDoNowAccentDark, Color.White, ZoneDoNowContainerDark)
        else ZoneColors(ZoneDoNowAccentLight, Color.White, ZoneDoNowContainerLight)

        PriorityZone.PLAN -> if (dark) ZoneColors(ZonePlanAccentDark, Color.White, ZonePlanContainerDark)
        else ZoneColors(ZonePlanAccentLight, Color.White, ZonePlanContainerLight)

        PriorityZone.IN_BETWEEN -> if (dark) ZoneColors(ZoneInBetweenAccentDark, Color(0xFF2B0A0A), ZoneInBetweenContainerDark)
        else ZoneColors(ZoneInBetweenAccentLight, Color.White, ZoneInBetweenContainerLight)

        PriorityZone.POSTPONE -> if (dark) ZoneColors(ZonePostponeAccentDark, Color.White, ZonePostponeContainerDark)
        else ZoneColors(ZonePostponeAccentLight, Color.White, ZonePostponeContainerLight)
    }
}
