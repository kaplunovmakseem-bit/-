package ru.taskpriority

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import ru.taskpriority.ui.navigation.AppNavigation
import ru.taskpriority.ui.theme.TaskPriorityTheme

/** Единственная Activity: включает тему и показывает граф навигации на Compose. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge() // контент рисуется под системными панелями, отступы даёт Scaffold
        setContent {
            TaskPriorityTheme {
                AppNavigation()
            }
        }
    }
}
