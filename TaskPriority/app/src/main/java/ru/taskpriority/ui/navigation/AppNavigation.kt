package ru.taskpriority.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ru.taskpriority.domain.PriorityZone
import ru.taskpriority.ui.edit.EditTaskScreen
import ru.taskpriority.ui.list.TaskListScreen
import ru.taskpriority.ui.matrix.MatrixScreen
import ru.taskpriority.ui.zone.ZoneScreen

/** Маршруты (адреса) экранов и их аргументы. */
object Routes {
    const val MATRIX = "matrix"
    const val LIST = "list"

    const val ARG_ZONE = "zone"
    const val ZONE = "zone/{$ARG_ZONE}"
    fun zone(zone: PriorityZone) = "zone/${zone.name}"

    const val ARG_TASK_ID = "taskId"
    const val NEW_TASK_ID = -1L
    /** Необязательный аргумент: без него открывается создание новой задачи. */
    const val EDIT = "edit?$ARG_TASK_ID={$ARG_TASK_ID}"
    fun edit(taskId: Long? = null) = if (taskId == null) "edit" else "edit?$ARG_TASK_ID=$taskId"
}

/** Граф навигации: какие экраны есть и как между ними переходить. */
@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Routes.MATRIX) {

        composable(Routes.MATRIX) {
            MatrixScreen(
                onOpenZone = { zone -> navController.navigate(Routes.zone(zone)) },
                onOpenList = { navController.navigate(Routes.LIST) },
                onAddTask = { navController.navigate(Routes.edit()) },
                onEditTask = { id -> navController.navigate(Routes.edit(id)) },
            )
        }

        composable(
            route = Routes.ZONE,
            arguments = listOf(navArgument(Routes.ARG_ZONE) { type = NavType.StringType }),
        ) {
            ZoneScreen(
                onBack = { navController.popBackStack() },
                onAddTask = { navController.navigate(Routes.edit()) },
                onEditTask = { id -> navController.navigate(Routes.edit(id)) },
            )
        }

        composable(Routes.LIST) {
            TaskListScreen(
                onBack = { navController.popBackStack() },
                onAddTask = { navController.navigate(Routes.edit()) },
                onEditTask = { id -> navController.navigate(Routes.edit(id)) },
            )
        }

        composable(
            route = Routes.EDIT,
            arguments = listOf(
                navArgument(Routes.ARG_TASK_ID) {
                    type = NavType.LongType
                    defaultValue = Routes.NEW_TASK_ID
                }
            ),
        ) {
            EditTaskScreen(onDone = { navController.popBackStack() })
        }
    }
}
